import { STIM_STATUS } from "./enums";

import { getDefaultProtocolEditorState } from "./getters";

export default {
  setSelectedWells(state, wells) {
    state.selectedWells = wells;
  },
  applySelectedProtocol(state, protocol) {
    state.selectedWells.map((well) => {
      state.protocolAssignments[well] = protocol;
    });

    const previousState = state.protocolAssignments;
    state.protocolAssignments = { ...state.protocolAssignments };
    state.selectedWells = [];

    if (Object.keys(previousState) !== Object.keys(state.protocolAssignments))
      // checks if indices are different because this mutation gets called when existing assignments get edited
      state.stimStatus = STIM_STATUS.CONFIG_CHECK_NEEDED;
  },
  clearSelectedProtocol(state) {
    state.selectedWells.map((well) => delete state.protocolAssignments[well]);
    state.protocolAssignments = { ...state.protocolAssignments };
    state.selectedWells = [];
    if (Object.keys(state.protocolAssignments).length === 0)
      state.stimStatus = STIM_STATUS.NO_PROTOCOLS_ASSIGNED;
  },
  setProtocolName({ protocolEditor }, name) {
    protocolEditor.name = name;
  },
  setStimulationType({ protocolEditor }, type) {
    if (type[0] === "C") protocolEditor.stimulationType = "C";
    if (type[0] === "V") protocolEditor.stimulationType = "V";
  },
  setRepeatColorAssignments(state, assignments) {
    state.repeatColors = assignments;
  },
  setZoomIn(state, axis) {
    if (axis === "y-axis") state.yAxisScale /= 1.5;
  },
  setZoomOut(state, axis) {
    if (axis === "y-axis") state.yAxisScale *= 1.5;
  },
  resetProtocolEditor(state) {
    // Tanner (8/8/22): could probably use this mutation in resetState to remove duplicate code
    const replaceState = {
      ...state,
      protocolEditor: getDefaultProtocolEditorState(),
      xAxisValues: [],
      yAxisValues: [],
      repeatColors: [],
      yAxisScale: 120,
      delayBlocks: [],
      xAxisTimeIdx: 0,
      editMode: { status: false, letter: "", label: "" },
    };
    Object.assign(state, replaceState);
  },
  resetState(state) {
    const replaceState = {
      ...state,
      selectedWells: [],
      protocolAssignments: {},
      protocolEditor: getDefaultProtocolEditorState(),
      xAxisValues: [],
      yAxisValues: [],
      repeatColors: [],
      yAxisScale: 120,
      delayBlocks: [],
      xAxisTimeIdx: 0,
      stimStatus: STIM_STATUS.NO_PROTOCOLS_ASSIGNED,
      editMode: { status: false, letter: "", label: "" },
    };
    Object.assign(state, replaceState);
  },
  setRestDuration({ protocolEditor }, time) {
    protocolEditor.restDuration = Number(time);
  },
  setDelayAxisValues(state, delay) {
    const { restDuration, subprotocols, timeUnit } = state.protocolEditor;

    const convertedDelayDuration = restDuration;
    const delayPulseModel = {
      type: "Delay",
      duration: restDuration,
      unit: timeUnit,
    };
    state.delayBlocks = [delay];
    if (!isNaN(convertedDelayDuration) && convertedDelayDuration !== 0) subprotocols.push(delayPulseModel);
  },
  setSubprotocols({ protocolEditor }, { subprotocols, newSubprotocolOrder }) {
    protocolEditor.subprotocols = subprotocols;
    protocolEditor.detailedSubprotocols = newSubprotocolOrder;
  },
  setAxisValues(state, { xValues, yValues }) {
    state.xAxisValues = xValues;
    state.yAxisValues = yValues;
  },
  setNewProtocol({ protocolList }, protocol) {
    protocolList.push(protocol);
  },
  setImportedProtocol({ protocolList }, protocol) {
    protocolList.push(protocol);
  },
  setStimPlayState(state, bool) {
    state.stimPlayState = bool;

    // this contradictory state occurs when 'Stimulate until complete' was selected for a stimulation.
    // the system status pinging returns a isStimulating key that constantly updates the stimPlayState
    // currently no other way set up for the FE to know on it's own that a stimulation has run to completion
    if (!state.stimPlayState && state.stimStatus === STIM_STATUS.STIM_ACTIVE)
      state.stimStatus = STIM_STATUS.READY;
  },
  setStimStatus(state, status) {
    if (
      Object.keys(state.protocolAssignments).length === 0 &&
      ![STIM_STATUS.ERROR, STIM_STATUS.SHORT_CIRCUIT_ERROR, STIM_STATUS.CONFIG_CHECK_COMPLETE].includes(
        status
      )
    )
      state.stimStatus = STIM_STATUS.NO_PROTOCOLS_ASSIGNED;
    else state.stimStatus = status;
  },
  setEditMode({ editMode }, { label, letter }) {
    editMode.status = true;
    editMode.label = label;
    editMode.letter = letter;
  },
  setEditModeOff({ editMode }) {
    editMode.status = false;
  },
  setStopSetting({ protocolEditor }, setting) {
    protocolEditor.runUntilStopped = setting;
  },
  setXAxisTimeIdx(state, idx) {
    state.xAxisTimeIdx = idx;
  },
  onPulseMouseleave(state) {
    state.hoveredPulse = {
      idx: null,
      indices: [],
      color: null,
    };
  },
  setStimulatorCircuitStatuses(state, stimulatorStatuses) {
    state.stimulatorCircuitStatuses = [...stimulatorStatuses];
  },
  setTimeUnit({ protocolEditor }, unit) {
    protocolEditor.timeUnit = unit;
  },
};
