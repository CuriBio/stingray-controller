"use strict";

/**
 * Function to convert json object to indexed array
 * @param   {Object} theJson The json object
 * @return  {Array}  The array of two numbers
 */
function convertFromJsonOfSampleIdxAndValue(theJson) {
  // javascript array of arrays takes up much more memory than numbers, so just have two separate arrays https://www.mattzeunert.com/2016/07/24/javascript-array-object-sizes.html
  const sampleIdxArr = new Array(theJson.length);
  const valueArr = new Array(theJson.length);
  theJson.forEach((thisJsonData, thisJsonIdx) => {
    const thisSampleIdx = parseInt(thisJsonData.sampleIdx);
    const thisValue = parseFloat(thisJsonData.value);

    sampleIdxArr[thisJsonIdx] = thisSampleIdx;
    valueArr[thisJsonIdx] = thisValue;
  });

  return { sampleIndices: sampleIdxArr, values: valueArr };
}

/**
 * Function to convert json object to indexed array
 * @param   {array} arr the array
 * @param   {int}  sampleIdxToMatch nearst matching idx
 * @return  {int}   closest idx value
 */
function findClosestArrayIdx(arr, sampleIdxToMatch) {
  // Modeled from https://stackoverflow.com/questions/22697936/binary-search-in-javascript
  // finds the array idx that has a sample idx >= the one searched for
  const maxIdx = arr.findIndex(xValue => xValue >= sampleIdxToMatch);
  return maxIdx >= 0 ? maxIdx : arr.length - 1;
}

/**
 * Function to convert json object to indexed array
 * @param   {array} xArray the array
 * @param   {array} yArray the array
 * @return  {array}  outputArray combined array
 */
function convertXYArraysToD3Array(xArray, yArray) {
  const outputArray = [];
  for (let i = 0; i < xArray.length; i++) {
    outputArray.push([xArray[i], yArray[i]]);
  }
  return outputArray;
}

/**
 * Function to convert json object to indexed array
 * @param   {array} sampleIndices the array
 * @param   {array} measuredValues the array
 * @param   {int}  startingSampleIdx
 * @param   {int}  sampleDurationToDisplay combined array
 * @param   {int}  wellIdx index
 * @return  {array} converted d3 array
 */
function getArraySliceToDisplay(
  sampleIndices,
  measuredValues,
  startingSampleIdx,
  sampleDurationToDisplay
) {
  // TODO (Eli 2/4/20): update the binary search to allow a manual setting of the start idx of the search, and update this to set that start when searching for the end idx (which should always be after the located start idx)
  let startingArrIdx = findClosestArrayIdx(sampleIndices, startingSampleIdx);
  if (sampleIndices[startingArrIdx] > startingSampleIdx) {
    if (startingArrIdx > 0) {
      // It is non-sensical to return a value below zero for the beginning of the slice
      startingArrIdx -= 1;
    }
  }
  const endingArrIdx = findClosestArrayIdx(
    sampleIndices,
    startingSampleIdx + sampleDurationToDisplay
  );

  const slicedXDataPoints = sampleIndices.slice(startingArrIdx, endingArrIdx + 1);
  const slicedYDataPoints = measuredValues.slice(startingArrIdx, endingArrIdx + 1);
  return convertXYArraysToD3Array(slicedXDataPoints, slicedYDataPoints);
}

/**
 * Function to convert json object to indexed array
 * @param   {Object} theWellJson the array
 * @param   {int}   wellNum number
 * @return  {array} converted  array
 */
function convertFromJsonOfWellIndicesAndXYArrays(theWellJson, wellNum) {
  const firstSimpleJsonWaveform = theWellJson["waveformDataPoints"][wellNum];

  const wellIdxArr = firstSimpleJsonWaveform["xDataPoints"];
  const wellValueArr = firstSimpleJsonWaveform["yDataPoints"];

  return { sampleIndices: wellIdxArr, values: wellValueArr };
}

/**
 * Function to convert json object to indexed array
 * @param   {Object} theWellJson the array
 * @param   {int}   wellNum number
 * @return  {array} converted  array
 */
function convertFromJsonOfWellIndicesToSparseArrays(theWellJson, wellNum) {
  const firstSimpleJsonWaveform = theWellJson["waveformDataPoints"][wellNum];

  const tempWellIdxArr = firstSimpleJsonWaveform["xDataPoints"];
  const tempWellValueArr = firstSimpleJsonWaveform["yDataPoints"];

  const lastElementXScale = tempWellIdxArr[tempWellIdxArr.length - 1];

  const wellValueSparseArr = new Array(lastElementXScale).fill(undefined);

  let count = 0;
  let i = 0;
  for (i = 0; i <= lastElementXScale; i++) {
    const thisValue = parseFloat(tempWellValueArr[count]);
    const sparseIdx = parseInt(tempWellIdxArr[count]);

    if (i == sparseIdx) {
      wellValueSparseArr[sparseIdx] = thisValue;
      count = count + 1;
    }
  }
  return { values: wellValueSparseArr };
}

/**
 * Function to convert json object to indexed array
 * @param   {array} arr the array
 * @param   {int}   sampleIdxToMatch number
 * @return  {int}   closest array index
 */
function findClosestWellIdx(arr, sampleIdxToMatch) {
  return findClosestArrayIdx(arr, sampleIdxToMatch);
}

/**
 * Function to convert json object to indexed array
 * @param   {array} sampleIndices the array
 * @param   {array} measuredValues the array
 * @param   {int}  startingSampleIdx
 * @param   {int}  sampleDurationToDisplay combined array
 * @return  {array} converted d3 array
 */
function getWellSliceToDisplay(
  sampleIndices,
  measuredValues,
  startingSampleIdx,
  sampleDurationToDisplay
) {
  return getArraySliceToDisplay(
    sampleIndices,
    measuredValues,
    startingSampleIdx,
    sampleDurationToDisplay
  );
}

/**
 * Function to append an array
 * @param   {array} arr the array
 * @param   {array} newArr the array
 * @return  {array} arr appended
 */
function appendWellData(arr, newArr) {
  const { waveformDataPoints } = newArr.waveformData.basicData;
  /* lint identifyies this as potential crash point as we not verifying if the
     innerObjectWaveformDataPoints is not null
     so with only if condition it allows so including the if condition as guard-for-in
     */

  for (const strWellIdx in waveformDataPoints) {
    if (waveformDataPoints != undefined) {
      const intWellIdx = parseInt(strWellIdx);
      Array.prototype.push.apply(
        arr[intWellIdx].xDataPoints,
        waveformDataPoints[strWellIdx].xDataPoints
      );
      Array.prototype.push.apply(
        arr[intWellIdx].yDataPoints,
        waveformDataPoints[strWellIdx].yDataPoints
      );
    }
  }

  return arr;
}

/**
 * Function to that returns a random, high-contrast color.
 * Currently, if a user duplicates a single pulse more than 4 times, it will start to rotate similar colors.
 * Similarly, if a user duplicates a pulse with two succeeding pulses after, the next color will be the same as the pulse two ahead of the duplicated pulse.
 * @param   {boolean} nonGreen request to remove non-green hues or not from random color generator
 * @param   {string} previousHue used to ensure previous color is different enough in hue to new random color
 * @param   {string} nextHue used to ensure succeeding color is different enough in hue to new random color
 * @return  {string} string hsla value
 */
function generateRandomColor(nonGreen, previousHue, nextHue) {
  let selectedHue;

  // remove green hues from color range 70-170
  const nonGreenRanges = [...Array(71).keys(), ...[...Array(360).keys()].splice(170)];

  if (nonGreen && previousHue) {
    // this case is when the previous pulse color needs to be considered in next selection
    const intHue = nextHue ? Number(nextHue) : Number(previousHue);
    const hueIdx = nonGreenRanges.indexOf(intHue);

    // 80 will prevent too similar of purple/blue and red/pink next to each other
    let oppositeIdx = hueIdx + 80;

    if (!nonGreenRanges[oppositeIdx]) {
      // using 210 instead of 260 (the total length of non-green hues) to prevent only alternating 4 colors
      oppositeIdx -= 210;
    }

    // assign selected hue
    selectedHue = nonGreenRanges[oppositeIdx];
  } else if (nonGreen && !previousHue) {
    // this is for the first pulse in a stimulation protocol when there is no previous color to consider
    // select random color from the non-green hues
    const randomNonGreenIdx = Math.floor(261 * Math.random());
    selectedHue = nonGreenRanges[randomNonGreenIdx];
  } else {
    // if green is allowed then just generate random color
    // this is used in the protocol letter and well assignment color, not any pulse colors
    selectedHue = 1 + Math.floor(359 * Math.random());
  }

  // Random non-green with high saturation, 50% lightness, and 100% opacity
  return `hsla(${selectedHue}, 100%, 50%, 1)`;
}

exports.convertFromJsonOfSampleIdxAndValue = convertFromJsonOfSampleIdxAndValue;
exports.findClosestArrayIdx = findClosestArrayIdx;
exports.getArraySliceToDisplay = getArraySliceToDisplay;
exports.convertFromJsonOfWellIndicesAndXYArrays = convertFromJsonOfWellIndicesAndXYArrays;
exports.convertFromJsonOfWellIndicesToSparseArrays = convertFromJsonOfWellIndicesToSparseArrays;
exports.findClosestWellIdx = findClosestWellIdx;
exports.getWellSliceToDisplay = getWellSliceToDisplay;
exports.convertXYArraysToD3Array = convertXYArraysToD3Array;
exports.appendWellData = appendWellData;
exports.generateRandomColor = generateRandomColor;
