# Rust Sheets – Spreadsheet Implementation Overview

## Data Structure

- **HashMap Structure:**
  - **Key:** `Coordinate` struct – Stores `x`, `y` positions as `u32`.
  - **Value:** `Cell` struct – Contains:
    - `cellValue`
    - Vector of dependency variables
    - Strings of Rhai expressions
    - `error` field

### Why HashMap Over 2D Vector?

- **Memory Efficiency:**
  - 2D vectors store empty cells unnecessarily. For example:
    - To store a value in `C3`, a 3x3 vector is required, even if other cells are empty.
    - A HashMap only stores cells with values, saving memory.

- **Dynamic Resizing Overhead:**
  - A 2D vector needs resizing when new values exceed its current size, which is computationally expensive.
  - HashMaps avoid this by growing dynamically without costly resizing operations.

---

## Function Overview

### Functions Handling Scalar, Vector, and Matrix Data Types

- **`lib.rs`:**
  - `fn var_to_cell_argument`

- **`helper.rs`:**
  - `fn check_cell_argument_error`
  - `fn matrix_contains_cell`

### Identified Code Duplication

1. **Cell Reference Parsing:**
   - Determining if a reference (e.g., `A3`, `A3_A4`) is scalar, vector, or matrix.
2. **Coordinate Extraction:**
   - Extracting the start and end coordinates from vector/matrix references.
3. **Data Retrieval Duplication:**
   - Matrix handling involves multiple vector-based data retrievals.
4. **Enum Handling Duplication:**
   - Redundant match cases for the three types of cell arguments.

### Possible Improvements

- **Introduce a `CellReference` Type:**
  - Encapsulates common operations like coordinate parsing.
  - Handles scalar, vector, and matrix distinctions internally.

- **Implement Custom Traits on Cell Arguments:**
  - Example: A `contains` function to determine if a cell lies within the bounds of a vector/matrix reference.

---

## Threading Considerations

### Current Multi-Threaded Implementation

- **Concurrency Setup:**
  - Uses `Arc` and `RwLock` to manage the shared HashMap (`Rsheet`).

    ```rust
    type RsheetClone = Arc<RwLock<Rsheet>>;
    let spreadsheet_clone: RsheetClone = Arc::clone(&spreadsheet_arc);
    let read_lock = spreadsheet.read().unwrap();
    let mut write_lock = spreadsheet.write().unwrap();
    ```

  - **Rationale:**
    - `Arc` ensures safe sharing of `Rsheet` across threads.
    - `RwLock` allows multiple readers and ensures exclusive write access when needed.

### Single-Threaded Alternative

- **Simplified Code Without Concurrency:**
  - No need for `Arc` or `RwLock`.
  - Example:

    ```rust
    let spreadsheet: Rsheet = HashMap::new();
    ```

  - **Benefits:**
    - Avoids cloning and locking overhead.
    - No risk of data races without concurrent execution.

---

## Handling `last_received` with Time-Based Consistency

- **Issue:** Ensure that only the latest `set` command updates the cell.
- **Solution:**
  1. Capture `Instant::now` **before** calling `runner.run`.
  2. If the cell's `last_received` is older than the current timestamp, update the cell.
  3. If the cell was already updated by another thread, discard the new value.

- **Reasoning:**  
  - Storing the timestamp before running `runner.run` ensures the latest command is always honored, even if there are concurrent `set` commands.

---

## Dependency Updates

### Current Single-Threaded Process

1. **Dependency Search:**  
   - Recursively find all dependent cells and add them to a queue.

2. **Queue Processing:**  
   - Iterate through the queue and update each cell sequentially.

### Multi-Threaded Approach

1. **Parallel Dependency Search:**  
   - Each recursive call spawns a new thread to search for dependencies.
   - `RwLock` ensures safe concurrent reads from the shared HashMap.

2. **Parallel Queue Processing:**
   - Use a worker pool to assign cells to threads for evaluation.
   - Each worker locks the sheet for writing **only after** evaluating (`runner.run`), minimizing blocking.

---

## Summary

Rust Sheets leverages a **HashMap** for memory-efficient storage and supports **multi-threaded execution** for performance. Code duplication in parsing and cell reference handling could be improved by introducing custom traits or a dedicated `CellReference` type. While multi-threading adds complexity, it ensures scalability by efficiently handling concurrent updates and dependency propagation.
