use rsheet_lib::connect::{Manager, Reader, Writer};
use rsheet_lib::replies::Reply;

use rsheet_lib::cell_value::CellValue;
use rsheet_lib::command_runner::{CellArgument, CommandRunner};
use std::collections::{HashMap, VecDeque};
use std::error::Error;
use std::sync::{Arc, RwLock, RwLockReadGuard, RwLockWriteGuard};
use std::thread;
use std::time::Instant;

mod helper;
use helper::{check_cell_argument_error, coord_to_str, matrix_contains_cell, str_to_coord};

#[derive(Hash, Eq, Clone, PartialEq)]
struct Coordinate {
    x: u32,
    y: u32,
}

#[derive(Clone, Debug)]
struct Cell {
    value: CellValue,
    last_received: Option<Instant>,
    expression: String,
    dependencies: Vec<String>,
    error: Option<String>,
}
impl Default for Cell {
    fn default() -> Self {
        Cell {
            value: CellValue::default(),
            last_received: None,
            expression: "".to_string(),
            dependencies: Vec::new(),
            error: None,
        }
    }
}

type Rsheet = HashMap<Coordinate, Cell>;
type RsheetClone = Arc<RwLock<Rsheet>>;

pub fn start_server<M>(mut manager: M) -> Result<(), Box<dyn Error>>
where
    M: Manager,
{
    let spreadsheet: Rsheet = HashMap::new();
    let spreadsheet_arc: RsheetClone = Arc::new(RwLock::new(spreadsheet));
    let mut threads: Vec<thread::JoinHandle<()>> = Vec::new();

    loop {
        let (mut recv, mut send) = match manager.accept_new_connection() {
            Ok(r) => r,
            Err(_) => break,
        };

        let spreadsheet_clone: RsheetClone = Arc::clone(&spreadsheet_arc);

        let new_thread = thread::spawn(move || {
            process_connection(&mut recv, &mut send, spreadsheet_clone);
        });
        threads.push(new_thread)
    }

    for thread in threads {
        let _ = thread.join();
    }
    Ok(())
}

fn process_connection<R, W>(recv: &mut R, send: &mut W, spreadsheet: RsheetClone)
where
    R: Reader,
    W: Writer,
{
    loop {
        let msg = match recv.read_message() {
            Ok(m) => m,
            Err(_) => return,
        };
        let _ = match run_command(&spreadsheet, &msg) {
            Some(r) => send.write_message(r),
            None => continue,
        };
    }
}

fn run_command(spreadsheet: &RsheetClone, command_str: &str) -> Option<Reply> {
    let mut split = command_str.split_whitespace();
    let command = match split.next() {
        Some(s) => s,
        None => {
            return Some(Reply::Error(format!(
                "Basic command missing: {}",
                command_str
            )))
        }
    };
    let cell = match split.next() {
        Some(s) => s,
        None => {
            return Some(Reply::Error(format!(
                "Cell reference missing: {}",
                command_str
            )))
        }
    };
    let args = split.collect::<Vec<&str>>().join(" ");

    match command {
        "get" => Some(get(spreadsheet, cell)),
        "set" => {
            if args.is_empty() {
                return Some(Reply::Error(format!(
                    "Set command requires an expression: {}",
                    command_str
                )));
            }
            set(spreadsheet, cell, &args)
        }
        _ => Some(Reply::Error(format!(
            "Unknown basic command: {}",
            command_str
        ))),
    }
}

fn get(spreadsheet: &RsheetClone, cell_str: &str) -> Reply {
    let coord = match str_to_coord(cell_str) {
        Ok(c) => c,
        Err(e) => return Reply::Error(e),
    };

    let read_lock = spreadsheet.read().unwrap();
    let cell = read_cell_from_coord(&read_lock, &coord);

    match cell.error {
        Some(e) => Reply::Error(e),
        None => Reply::Value(cell_str.to_string(), cell.value),
    }
}

// find cell in spreadsheet according to coordinate struct
// this uses a readlock
fn read_cell_from_coord(read_hash: &RwLockReadGuard<Rsheet>, coord: &Coordinate) -> Cell {
    // have to clone cell because reply in get fn requires a cell
    // if i return cell, its moved out of spreadsheet hashmap,
    // then data is not maintained
    let value: Cell = match read_hash.get(coord) {
        Some(c) => c.clone(),
        None => Cell::default(),
    };
    value
}

fn write_cell_from_coord(
    write_hash: &mut RwLockWriteGuard<Rsheet>,
    coordinate: Coordinate,
    cell: Cell,
) {
    write_hash.insert(coordinate, cell);
}

fn set(spreadsheet: &RsheetClone, cell_str: &str, args: &str) -> Option<Reply> {
    let msg_time = Instant::now();

    let coord = match helper::str_to_coord(cell_str) {
        Ok(c) => c,
        Err(e) => return Some(Reply::Error(e)),
    };

    let runner = CommandRunner::new(args);
    let variables = runner.find_variables();
    let mut variables_hash: HashMap<String, CellArgument> = HashMap::new();

    let read_lock = spreadsheet.read().unwrap();
    for var in &variables {
        let temp_val = match var_to_cell_argument(&read_lock, var) {
            Ok(ca) => ca,
            Err(e) => return Some(Reply::Error(e)),
        };
        variables_hash.insert(var.to_string(), temp_val);
    }
    drop(read_lock);

    let eval = runner.run(&variables_hash);

    // check if current message was latest
    // if not latest, then return
    let read_lock = spreadsheet.read().unwrap();
    let existing = read_cell_from_coord(&read_lock, &coord);
    drop(read_lock);

    if let Some(old_time) = existing.last_received {
        if old_time > msg_time {
            return None;
        }
    }

    let error: Option<String> = match check_cell_argument_error(&variables_hash) {
        true => Some("Cell relies on another cell with an error".to_string()),
        false => None,
    };

    let mut write_lock = spreadsheet.write().unwrap();
    write_cell_from_coord(
        &mut write_lock,
        coord,
        Cell {
            value: eval,
            last_received: Some(msg_time),
            expression: args.to_string(),
            dependencies: variables,
            error,
        },
    );
    drop(write_lock);

    // need to update all dependencies based on this new cell
    let spreadsheet_clone = Arc::clone(spreadsheet);
    let dependency = cell_str.to_string();
    thread::spawn(move || {
        update_dependencies(spreadsheet_clone, dependency);
    });

    None
}

fn update_dependencies(spreadsheet: RsheetClone, cell_str: String) {
    let mut needs_update: VecDeque<Coordinate> = VecDeque::new();

    // get first cell to keep track of Self-Referential dependencies
    let myself = match str_to_coord(&cell_str) {
        Ok(c) => c,
        Err(_) => return,
    };

    let read_lock = spreadsheet.read().unwrap();
    let u = get_required_updates(&read_lock, &cell_str, &mut needs_update, &myself);
    drop(read_lock);

    match u {
        Ok(_) => {}
        Err(e) => {
            // origin also contains error
            needs_update.push_back(myself);

            let mut write_lock = spreadsheet.write().unwrap();
            for coord in needs_update {
                let cell = write_lock.get_mut(&coord).unwrap();
                cell.error = Some(e.to_string());
            }
            drop(write_lock);
            return;
        }
    }

    //iterate through update list and update dependencies
    update_cell(&spreadsheet, needs_update);
}

// finds cells that requires updating
// this is recursive
fn get_required_updates(
    read_lock: &RwLockReadGuard<Rsheet>,
    cell_str: &str,
    update_vec: &mut VecDeque<Coordinate>,
    origin: &Coordinate,
) -> Result<(), String> {
    // iterate through cells
    // find cells with cell_str as a dependency
    // if found add to queue
    for (coordinate, cell) in read_lock.iter() {
        for dep in cell.dependencies.iter() {
            //found cell with dependency
            if matrix_contains_cell(dep, cell_str) {
                if coordinate == origin {
                    return Err("Cell is self-referential".to_string());
                } else {
                    update_vec.push_back(coordinate.clone());
                    get_required_updates(read_lock, &coord_to_str(coordinate), update_vec, origin)?;
                }
            }
        }
    }
    Ok(())
}

fn update_cell(spreadsheet: &RsheetClone, update_vec: VecDeque<Coordinate>) {
    for coord in update_vec {
        let read_lock = spreadsheet.read().unwrap();
        let cell = read_lock.get(&coord).unwrap();

        let runner = CommandRunner::new(&cell.expression);
        let variables = runner.find_variables();
        let mut variables_hash: HashMap<String, CellArgument> = HashMap::new();

        for var in &variables {
            let temp_val = var_to_cell_argument(&read_lock, var).unwrap();
            variables_hash.insert(var.to_string(), temp_val);
        }
        drop(read_lock);
        let eval = runner.run(&variables_hash);
        let error: Option<String> = match check_cell_argument_error(&variables_hash) {
            true => Some("Cell relies on another cell with an error".to_string()),
            false => None,
        };

        let mut write_lock = spreadsheet.write().unwrap();
        let cell = write_lock.get_mut(&coord).unwrap();
        cell.value = eval;
        cell.error = error;
        drop(write_lock);
    }
}

fn var_to_cell_argument(
    read_lock: &RwLockReadGuard<Rsheet>,
    var_str: &str,
) -> Result<CellArgument, String> {
    if !var_str.contains('_') {
        let temp_coord = str_to_coord(var_str)?;
        let cell = read_cell_from_coord(read_lock, &temp_coord);
        return Ok(CellArgument::Value(cell.value));
    }

    let mut cells = var_str.split('_');
    let start = match cells.next() {
        Some(s) => s,
        None => return Err(format!("Missing cell at matrix start: {}", var_str)),
    };
    let end = match cells.next() {
        Some(s) => s,
        None => return Err(format!("Missing cell at matrix end: {}", var_str)),
    };

    let start_coord = str_to_coord(start)?;
    let end_coord = str_to_coord(end)?;

    if start_coord.y == end_coord.y {
        let mut vector: Vec<CellValue> = Vec::new();

        for i in start_coord.x..=end_coord.x {
            let temp_coord = Coordinate {
                x: i,
                y: start_coord.y,
            };
            vector.push(read_cell_from_coord(read_lock, &temp_coord).value);
        }

        Ok(CellArgument::Vector(vector))
    } else {
        let mut matrix: Vec<Vec<CellValue>> = Vec::new();
        for i in start_coord.y..=end_coord.y {
            let mut vector: Vec<CellValue> = Vec::new();
            for j in start_coord.x..=end_coord.x {
                let temp_coord = Coordinate { x: j, y: i };
                vector.push(read_cell_from_coord(read_lock, &temp_coord).value);
            }
            matrix.push(vector);
        }
        Ok(CellArgument::Matrix(matrix))
    }
}
