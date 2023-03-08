import { WellTitle } from "@/js-utils/LabwareCalculations.js";
import { WellTitle as LabwareDefinition } from "@/js-utils/LabwareCalculations.js"; // creating alias now for eventual transition to calling it LabwareDefinition (to match Python)
import { WellTitle as DistWellTitle } from "@/dist/stingray.common";

const wellTitleThreeCrossFour = new WellTitle(3, 4);
const wellTitleEightCrossTwelve = new WellTitle(8, 12);
const wellTitleSixteenCrossTwentyfour = new WellTitle(16, 24);

const wellTitleSixCrossTwelve = new DistWellTitle(6, 12);
describe("LabwareDefinition", () => {
  test("Given a 3x4 plate, When called at index 0 with padZeros set to False, Then return the well name without extra zeros", () => {
    const title = wellTitleThreeCrossFour.getWellNameFromWellIndex(0, false);
    expect(title).toStrictEqual("A1");
  });

  test("Given a 3x4 plate, When called at index 0 with padZeros set to True, Then return the well name with a padded zero", () => {
    const title = wellTitleThreeCrossFour.getWellNameFromWellIndex(0, true);
    expect(title).toStrictEqual("A01");
  });

  test("Given a 8x12 plate, When called at the last well with padZeros set to False, Then return the well name without extra zeros", () => {
    const title = wellTitleEightCrossTwelve.getWellNameFromWellIndex(95, false);
    expect(title).toStrictEqual("H12");
  });

  test("Given a 16x24 plate, When called at a well not the first or last with padZeros set to False, Then return the well name without extra zeros", () => {
    const title = wellTitleSixteenCrossTwentyfour.getWellNameFromWellIndex(2, false);
    expect(title).toStrictEqual("C1");
  });

  test("Given a 6x12 plate, When called at a well not the first or the last with padZeros set to False, Then return the well name without extra zeros", () => {
    const title = wellTitleSixCrossTwelve.getWellNameFromWellIndex(18, false);
    expect(title).toStrictEqual("A4");
  });

  test("Given a 6x12 plate, When called at the first well with padZeros set to True, Then return the well name with extra zeros", () => {
    const title = wellTitleSixCrossTwelve.getWellNameFromWellIndex(0, true);
    expect(title).toStrictEqual("A01");
  });

  test.each([
    [4, 6, 0, 0, 0],
    [4, 6, 23, 3, 5],
    [4, 6, 10, 2, 2],
    [8, 12, 0, 0, 0],
    [8, 12, 95, 7, 11],
    [8, 12, 27, 3, 3],
  ])(
    "Given a LabwareDefinition with %s rows and %s columns, When getRowAndColumnFromWellIndex is called with well index %s, Then the correct well rows and columns are returned",
    async (labwareNumRows, labwareNumColumns, wellIdxToTest, expectedRow, expectedColumn) => {
      const testDefinition = new LabwareDefinition(labwareNumRows, labwareNumColumns);
      const actualReturn = testDefinition.getRowAndColumnFromWellIndex(wellIdxToTest);
      expect(actualReturn.rowNum).toStrictEqual(expectedRow);
      expect(actualReturn.columnNum).toStrictEqual(expectedColumn);
    }
  );

  test.each([
    [0, 6, "Invalid number of rows: 0"],
    [-1, 9, "Invalid number of rows: -1"],
    [3, 0, "Invalid number of columns: 0"],
    [19, 2, "Invalid number of rows: 19"],
    [4, 37, "Invalid number of columns: 37"],
  ])(
    "Given a LabwareDefinition with %s rows and %s columns, When validateRowAndColumnCounts is called, Then it throws an error",
    async (labwareNumRows, labwareNumColumns, expectedErrorMatch) => {
      const testDefinition = new LabwareDefinition(labwareNumRows, labwareNumColumns);
      expect(() => {
        testDefinition.validateRowAndColumnCounts();
      }).toThrow(expectedErrorMatch);
    }
  );

  test.each([
    [4, 6, 0, 0, 0],
    [4, 6, 3, 5, 23],
    [4, 6, 2, 2, 10],
    [8, 12, 0, 0, 0],
    [8, 12, 7, 11, 95],
    [8, 12, 3, 3, 27],
  ])(
    "Given a LabwareDefinition with %s rows and %s columns, When getWellIdxFromRowAndColumn is called with row %s and column %s, Then the correct well index is returned",
    async (labwareNumRows, labwareNumColumns, rowToTest, columnToTest, expectedIdx) => {
      const testDefinition = new LabwareDefinition(labwareNumRows, labwareNumColumns);
      const actual = testDefinition.getWellIdxFromRowAndColumn(rowToTest, columnToTest);
      expect(actual).toStrictEqual(expectedIdx);
    }
  );
});
