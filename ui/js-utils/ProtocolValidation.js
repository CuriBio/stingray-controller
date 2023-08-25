import {
  MIN_SUBPROTOCOL_DURATION_MS,
  TIME_CONVERSION_TO_MILLIS,
  MAX_SUBPROTOCOL_DURATION_MS,
  MIN_CHARGE_MA,
  MAX_CHARGE_MA,
  MIN_PHASE_DURATION_US,
} from "@/store/modules/stimulation/enums";

export const DEFAULT_SUBPROTOCOL_TEMPLATES = {
  DELAY: {
    type: "Delay",
    color: "",
    pulseSettings: { duration: "", unit: "milliseconds" },
    subprotocols: [],
  },
  MONOPHASIC: {
    type: "Monophasic",
    color: "",
    pulseSettings: {
      frequency: "",
      totalActiveDuration: { duration: "", unit: "milliseconds" },
      numCycles: "",
      postphaseInterval: "",
      phaseOneDuration: "",
      phaseOneCharge: "",
    },
    subprotocols: [],
  },
  BIPHASIC: {
    type: "Biphasic",
    color: "",
    pulseSettings: {
      frequency: "",
      totalActiveDuration: { duration: "", unit: "milliseconds" },
      numCycles: "",
      postphaseInterval: "",
      phaseOneDuration: "",
      phaseOneCharge: "",
      interphaseInterval: "",
      phaseTwoCharge: "",
      phaseTwoDuration: "",
    },
    subprotocols: [],
  },
};

const invalidErrMsg = {
  numErr: "Must be a number",
  required: "Required",
  maxPulseDuration: "Duration must be <= 50ms",
  minPulseDuration: `Duration must be >= ${MIN_PHASE_DURATION_US}μs`,
  minInterphaseDuration: `Duration must be 0ms or >= ${MIN_PHASE_DURATION_US}μs`,
  minActiveDuration: "Duration must be >= 100ms",
  valid: "",
  maxMinCurrent: `Must be within [-${MIN_CHARGE_MA}, -${MAX_CHARGE_MA}] or [${MIN_CHARGE_MA}, ${MAX_CHARGE_MA}]`,
  frequency: "Must be a non-zero value <= 100",
  numCycles: "Must be a whole number > 0",
  minDelayDuration: `Duration must be >=${MIN_SUBPROTOCOL_DURATION_MS}ms`,
  maxDelayDuration: "Duration must be <= 24hrs",
  delayNumErr: "Must be a (+) number",
  nonInteger: "Must be a whole number of ms",
};

export const checkNumCyclesValidity = (numCycles) => {
  // check if value is a whole number greater than 0
  const errorMsgLabel =
    numCycles === "" || !Number.isInteger(+numCycles) || +numCycles <= 0 ? "numCycles" : "valid";
  return invalidErrMsg[errorMsgLabel];
};

export const checkPulseChargeValidity = (valueStr) => {
  let errorMessage;
  // if empty
  if (valueStr === "") {
    errorMessage = invalidErrMsg.required;
    // else if not a number
  } else if (isNaN(+valueStr)) {
    errorMessage = invalidErrMsg.numErr;
    // else if it's a current controlled stim and the value is not within [+/-1, +/-100]
  } else if (Math.abs(+valueStr) > MAX_CHARGE_MA || Math.abs(+valueStr) < MIN_CHARGE_MA) {
    errorMessage = invalidErrMsg.maxMinCurrent;
    // else valid
  } else {
    errorMessage = invalidErrMsg.valid;
  }

  return errorMessage;
};

export const checkPulseDurationValidity = (
  valueStr,
  isInterphaseDur,
  maxPulseDurationForFreq,
  totalPulseDuration
) => {
  const isValueLessThanMin = +valueStr < MIN_PHASE_DURATION_US / 1000;
  let errorMessage;

  // if empty
  if (valueStr === "") {
    errorMessage = invalidErrMsg.required;
    // else if value is not a valid number
  } else if (isNaN(+valueStr)) {
    errorMessage = invalidErrMsg.numErr;
    // else if value is less than allowed minimum and no interphase interval because interphase has it's own limits
  } else if (isValueLessThanMin && !isInterphaseDur) {
    errorMessage = invalidErrMsg.minPulseDuration;
    // else if it is interphase interval and value is less than min and not 0
  } else if (isValueLessThanMin && +valueStr !== 0 && isInterphaseDur) {
    errorMessage = invalidErrMsg.minInterphaseDuration;
    // else total duration of all durations is too high for the frequency input
  } else if (totalPulseDuration > maxPulseDurationForFreq) {
    errorMessage = invalidErrMsg.maxPulseDuration;
    // else valid
  } else {
    errorMessage = invalidErrMsg.valid;
  }

  return errorMessage;
};

export const checkActiveDurationValidity = (valueStr, selectedUnit, totalPulseDuration) => {
  const valueInMillis = +valueStr * TIME_CONVERSION_TO_MILLIS[selectedUnit];
  const minDurAllowed = Math.max(MIN_SUBPROTOCOL_DURATION_MS, totalPulseDuration || 0);
  let errorMessage;

  // if empty
  if (valueStr === "") {
    errorMessage = invalidErrMsg.required;
    // else if not a valid number
  } else if (isNaN(+valueStr)) {
    errorMessage = "Invalid number";
    // else if value is less than allowed minimum
  } else if (valueInMillis < minDurAllowed) {
    errorMessage = `Must be >= ${minDurAllowed}ms`;
    // else if value is greater than allowed maximum
  } else if (valueInMillis > MAX_SUBPROTOCOL_DURATION_MS) {
    const maxInHrs = MAX_SUBPROTOCOL_DURATION_MS / TIME_CONVERSION_TO_MILLIS.hours;
    errorMessage = `Must be <= ${maxInHrs}hrs`;

    // else valid
  } else {
    errorMessage = invalidErrMsg.valid;
  }

  return errorMessage;
};

export const checkPulseFrequencyValidity = (valueStr, maxPulseDurForFreq) => {
  let errorMessage;
  // if empty
  if (valueStr === "") {
    errorMessage = invalidErrMsg.required;
    // else if not a number or is less than the minimum or greater than the maximum
  } else if (isNaN(+valueStr) || +valueStr <= 0 || +valueStr > 100) {
    errorMessage = invalidErrMsg.frequency;
    // else valid and set max pulse duration error message if needed
  } else {
    errorMessage = invalidErrMsg.valid;
    invalidErrMsg.maxPulseDuration = `Duration must be <= ${maxPulseDurForFreq}ms`;
  }
  return errorMessage;
};

export const checkDelayPulseValidity = (valueStr, selectedUnit) => {
  const valueInMillis = +valueStr * TIME_CONVERSION_TO_MILLIS[selectedUnit];
  let errorMessage;

  if (valueStr === "") {
    errorMessage = invalidErrMsg.required;
  } else if (isNaN(+valueStr)) {
    errorMessage = invalidErrMsg.delayNumErr;
  } else if (valueInMillis < MIN_SUBPROTOCOL_DURATION_MS) {
    errorMessage = invalidErrMsg.minDelayDuration;
  } else if (valueInMillis > MAX_SUBPROTOCOL_DURATION_MS) {
    errorMessage = invalidErrMsg.maxDelayDuration;
  } else if (!Number.isInteger(valueInMillis)) {
    errorMessage = invalidErrMsg.nonInteger;
  } else {
    errorMessage = invalidErrMsg.valid;
  }

  return errorMessage;
};

export const getMaxPulseDurationForFreq = (freq) => {
  return Math.min(50, Math.trunc((1000 / freq) * 0.8));
};

export const getTotalActiveDuration = (type, protocol) => {
  return type === "Monophasic"
    ? +protocol.phaseOneDuration
    : +protocol.phaseOneDuration + +protocol.phaseTwoDuration + +protocol.interphaseInterval;
};

export const calculateNumCycles = (selectedUnit, totalActiveDuration, pulseFrequency) => {
  const durationInSecs = totalActiveDuration.duration * (TIME_CONVERSION_TO_MILLIS[selectedUnit] / 1000);
  const numCycles = durationInSecs * pulseFrequency;
  return isFinite(numCycles) ? numCycles : "";
};

export const areValidPulses = (subprotocols) => {
  return subprotocols.some((proto) => {
    if (proto.type === "loop") return areValidPulses(proto.subprotocols);
    else return proto.type === "Delay" ? !_isValidDelayPulse(proto) : !_isValidSinglePulse(proto);
  });
};

export const _isValidSinglePulse = (protocol) => {
  const { duration, unit } = protocol.totalActiveDuration;
  const isMonophasic = protocol.type === "Monophasic";
  const chargesToCheck = isMonophasic ? ["phaseOneCharge"] : ["phaseOneCharge", "phaseTwoCharge"];
  const durationsToCheck = isMonophasic
    ? ["phaseOneDuration"]
    : ["phaseOneDuration", "phaseTwoDuration", "interphaseInterval"];

  const maxPulseDurationForFreq = getMaxPulseDurationForFreq(protocol.frequency);
  const totalActiveDuration = getTotalActiveDuration(protocol.type, protocol);

  // first check all durations are within max and min bounds
  const durationsAreValid =
    durationsToCheck.filter(
      (duration) =>
        checkPulseDurationValidity(
          protocol[duration],
          duration === "interphaseInterval",
          maxPulseDurationForFreq,
          totalActiveDuration
        ) !== ""
    ).length === 0;

  // check if charges are within max and min bounds
  const chargesAreValid =
    chargesToCheck.filter((charge) => checkPulseChargeValidity(protocol[charge]) !== "").length === 0;

  const completePulseValidity =
    checkPulseFrequencyValidity(protocol.frequency, maxPulseDurationForFreq) === "" &&
    checkActiveDurationValidity(duration, unit, totalActiveDuration) === "" &&
    checkNumCyclesValidity(protocol.numCycles) === "";

  return durationsAreValid && chargesAreValid && completePulseValidity;
};

export const _isValidDelayPulse = (protocol) => {
  const { duration, unit } = protocol;
  return checkDelayPulseValidity(duration, unit) === "";
};

export const convertProtocolCasing = (input, conversionFn) => {
  if (_isObject(input)) {
    if (!Array.isArray(input)) {
      input = conversionFn(input);
      for (const key in input) {
        if (_isObject(input[key])) {
          input[key] = convertProtocolCasing(input[key], conversionFn);
        }
      }
    } else {
      for (const [idx, obj] of Object.entries(input)) {
        const newObj = convertProtocolCasing(obj, conversionFn);
        input[idx] = newObj;
      }
    }
  }
  return input;
};

const _isObject = (input) => typeof input === "object";

export const _convertObjToCamelCase = (obj) => {
  const convertedObj = {};
  for (const [key, value] of Object.entries(obj)) {
    const camelCaseKey = key.replace(/_([a-z])/g, (matchedLetter) => matchedLetter[1].toUpperCase());
    convertedObj[camelCaseKey] = value;
  }

  return convertedObj;
};

export const _convertObjToSnakeCase = (obj) => {
  const convertedObj = {};

  for (const [key, value] of Object.entries(obj)) {
    const snakeCaseKey = key.replace(/[A-Z]/g, (letter) => `_${letter.toLowerCase()}`);
    convertedObj[snakeCaseKey] = value;
  }

  return convertedObj;
};

export const checkPulseCompatibility = (protocol) => {
  // if up-to-date protocol, just return
  if ("subprotocols" in protocol) return protocol;

  // grab protocol name, stim type, rest dur and unit
  const { name, restDuration, timeUnit, stimulationType } = protocol;
  // build new protocol
  const runUntilStopped = protocol.stopSetting.includes("Stopped");
  const compatibleSubprotocols = _convertDetailedSubprotocols(protocol.detailedPulses);

  return {
    name,
    restDuration,
    timeUnit,
    runUntilStopped,
    stimulationType,
    subprotocols: compatibleSubprotocols.map(({ subprotocol }) => subprotocol),
    detailedSubprotocols: compatibleSubprotocols.map(({ detailedSubprotocol }) => detailedSubprotocol),
  };
};

const _convertDetailedSubprotocols = (subprotocols) => {
  return subprotocols.map((pulse) => {
    switch (pulse.type) {
      case "Monophasic":
        return _createCompatiblePulse(pulse, "MONOPHASIC");
      case "Biphasic":
        return _createCompatiblePulse(pulse, "BIPHASIC");
      case "Delay":
        return _createCompatibleDelay(pulse);
    }
  });
};

const _createCompatibleDelay = (pulse) => {
  const detailedSubprotocol = JSON.parse(JSON.stringify(DEFAULT_SUBPROTOCOL_TEMPLATES.DELAY));
  // update color
  detailedSubprotocol.color = pulse.repeat.color;
  // update delay duration and unit
  Object.assign(detailedSubprotocol.pulseSettings, pulse.stimSettings.totalActiveDuration);

  return {
    detailedSubprotocol,
    subprotocol: {
      type: detailedSubprotocol.type,
      ...detailedSubprotocol.pulseSettings,
    },
  };
};

const _createCompatiblePulse = (pulse, type) => {
  const detailedSubprotocol = JSON.parse(JSON.stringify(DEFAULT_SUBPROTOCOL_TEMPLATES[type]));
  // update color
  detailedSubprotocol.color = pulse.repeat.color;
  // match any keys that are in both object structures
  for (const key of Object.keys(detailedSubprotocol.pulseSettings)) {
    if (key in pulse.pulseSettings) {
      detailedSubprotocol.pulseSettings[key] = pulse.pulseSettings[key];
    }
  }
  // update frequency
  detailedSubprotocol.pulseSettings.frequency = pulse.repeat.numberOfRepeats;
  // update total active duration
  Object.assign(
    detailedSubprotocol.pulseSettings.totalActiveDuration,
    pulse.stimSettings.totalActiveDuration
  );
  // update postphase interval
  detailedSubprotocol.pulseSettings.postphaseInterval = pulse.stimSettings.repeatDelayInterval;
  // udpate num cycles
  const { totalActiveDuration, frequency } = detailedSubprotocol.pulseSettings;

  detailedSubprotocol.pulseSettings.numCycles = calculateNumCycles(
    totalActiveDuration.unit,
    totalActiveDuration,
    frequency
  );

  return {
    detailedSubprotocol,
    subprotocol: {
      type: detailedSubprotocol.type,
      ...detailedSubprotocol.pulseSettings,
    },
  };
};
/*
    BIPHASIC
    ^^^^^^^^
    frequency
    interphaseInterval
    numCycles
    phaseOneCharge
    phaseOneDuration
    phaseTwoCharge
    phaseTwoDuration
    postphaseInterval
    totalActiveDuration
      duration
      unit
    type
  */

/*
    MONOPHASIC
    ^^^^^^^^^^
    frequency
    numCycles
    phaseOneCharge
    phaseOneDuration
    postphaseInterval
    totalActiveDuration
      duration
      unit
    type
  */

/*
    DELAY
    ^^^^^
    duration
    type
    unit

  */

/*
    LOOP
    ^^^^^
    numIterations: int
    type
    subprotocols: []

  */
