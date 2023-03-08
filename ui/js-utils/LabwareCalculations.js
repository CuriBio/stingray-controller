"use strict";

/**
 * Add an extra leading zero when needed to the number (for use in the well name)
 *
 * @param {int} columnIdx - The column index within the labware
 * @param {bool} padding - Whether to zero-pad the number in the well name
 * @return {string}
 */
function getFormattedColumnString(columnIdx, padding) {
  const columnNumber = columnIdx + 1;
  if (padding) {
    return "0" + columnNumber;
  } else {
    return columnNumber.toString();
  }
}

/** Allows calculations to convert between row, column, well index, and well name for Labware Definitions */
export class WellTitle {
  /**
   * Take pixel coordinates from a drawing and convert it back to the x/y numerical values that should have been used to generate those pixel coordinates.
   *
   * @param {int} numRows - The number of rows in the labware/plate
   * @param {int} numColumns - The number of columns in the labware/plate
   */
  constructor(numRows, numColumns) {
    this.numRows = numRows;
    this.numColumns = numColumns;
  }

  /**
   * Take pixel coordinates from a drawing and convert it back to the x/y numerical values that should have been used to generate those pixel coordinates.
   *
   * @throws {Error} If row or column index outside acceptable range (0-36 and 0-18) up to a 1536 well plate.
   */
  validateRowAndColumnCounts() {
    if (this.numRows < 1 || this.numRows > 18) {
      throw new Error(`Invalid number of rows: ${this.numRows}`);
    }
    if (this.numColumns < 1 || this.numColumns > 36) {
      throw new Error(`Invalid number of columns: ${this.numColumns}`);
    }
  }

  /**
   * Get the well name from the row and column indices
   *
   * @param {int} rowIdx - The row index within the labware
   * @param {int} columnIdx - The column index within the labware
   * @param {bool} padding - Whether to zero-pad the number in the well name
   * @return {string}
   */
  getWellNameFromRowAndColumn(rowIdx, columnIdx, padding) {
    const rowChar = String.fromCharCode(65 + rowIdx);
    const columnChar = getFormattedColumnString(columnIdx, padding);
    return rowChar + columnChar;
  }

  /**
   * Get the row and column indices from the well index
   *
   * @param {int} wellIdx - The well index within the labware
   * @return {Object} containing both the row index and well index (integers)
   */
  getRowAndColumnFromWellIndex(wellIdx) {
    const combo = {
      rowNum: 0,
      columnNum: 0,
    };
    this.validateRowAndColumnCounts();
    combo.rowNum = wellIdx % this.numRows;
    combo.columnNum = Math.floor(wellIdx / this.numRows);
    return combo;
  }

  /**
   * Get the alphanumeric well name from the well index
   *
   * @param {int} wellIdx - The well index within the labware
   * @param {bool} padding - Whether to zero-pad the number in the well name
   * @return {string} containing both the row index and well index (integers)
   */
  getWellNameFromWellIndex(wellIdx, padding) {
    let rowIdx = 0;
    let columnIdx = 0;
    const cellCombo = this.getRowAndColumnFromWellIndex(wellIdx);

    rowIdx = cellCombo.rowNum;
    columnIdx = cellCombo.columnNum;

    return this.getWellNameFromRowAndColumn(rowIdx, columnIdx, padding);
  }

  /**
   * Get the well index from the row and column indices
   *
   * @param {int} rowIdx - The row index within the labware
   * @param {int} columnIdx - The column index within the labware
   * @return {int}
   */
  getWellIdxFromRowAndColumn(rowIdx, columnIdx) {
    return columnIdx * this.numRows + rowIdx;
  }
}
