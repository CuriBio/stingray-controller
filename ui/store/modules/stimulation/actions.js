import { WellTitle as LabwareDefinition } from "@/js-utils/LabwareCalculations.js";
const twentyFourWellPlateDefinition = new LabwareDefinition(4, 6);
import { STIM_STATUS, TIME_CONVERSION_TO_MILLIS, COLOR_PALETTE } from "./enums";
import {
  areValidPulses,
  convertProtocolCasing,
  checkPulseCompatibility,
  _convertObjToCamelCase,
  _convertObjToSnakeCase,
  _convertSubprotocolsFromFw,
  _convertDetailedSubprotocolsFromFW,
} from "@/js-utils/ProtocolValidation";
import { SYSTEM_STATUS } from "@/store/modules/system/enums";

export default {
  handleSelectedWells({ commit }, wells) {
    const wellValues = [];

    wells.filter((well, idx) => {
      if (well) wellValues.push(idx);
    });

    commit("setSelectedWells", wellValues);
  },

  async handleProtocolOrder({ commit, dispatch, state }, newSubprotocolOrder) {
    const xValues = [0];
    const yValues = [0];
    const colorAssignments = [];
    const subprotocols = [];
    const getLast = (array) => array[array.length - 1];
    const helper = (setting, type) => {
      let componentsToAdd = [];
      if (type === "Delay") {
        componentsToAdd = {
          x: [setting.duration * TIME_CONVERSION_TO_MILLIS[setting.unit]],
          y: [0],
        };
      } else {
        // Add values for phase 1
        componentsToAdd = {
          x: [setting.phaseOneDuration],
          y: [setting.phaseOneCharge],
        };
        // If biphasic, handle remaining pulse components
        if (setting.phaseTwoDuration != null) {
          // Add values for interphase interval
          componentsToAdd.x.push(setting.interphaseInterval);
          componentsToAdd.y.push(0);
          // Add values for phase 2
          componentsToAdd.x.push(setting.phaseTwoDuration);
          componentsToAdd.y.push(setting.phaseTwoCharge);
        }
        // Add values for delay
        componentsToAdd.x.push(setting.postphaseInterval);
        componentsToAdd.y.push(0);
      }
      const numComponentsToAdd = componentsToAdd.x.length;
      // add components until all are added or the total active duration is reached
      for (let i = 0; i < numComponentsToAdd; i++) {
        const componentDuration = componentsToAdd.x[i];

        xValues.push(getLast(xValues), componentDuration + getLast(xValues));
        yValues.push(componentsToAdd.y[i], componentsToAdd.y[i]);
      }
      // set final value to zero in case the pulse was cut off in the middle of either phase
      xValues.push(getLast(xValues));
      yValues.push(0);
    };

    await newSubprotocolOrder.map(async (pulse) => {
      if (pulse.type !== "loop") {
        const { color } = pulse;
        let settings = pulse.pulseSettings;
        const startingRepeatIdx = xValues.length - 1;

        settings = {
          type: pulse.type,
          ...settings,
        };

        subprotocols.push(settings);

        // numCycles defaults to 0 and delay will never update unless run through once
        let remainingPulseCycles = pulse.type === "Delay" ? 1 : settings.numCycles;

        while (remainingPulseCycles > 0) {
          helper(settings, pulse.type);
          remainingPulseCycles--;
        }

        const endingRepeatIdx = xValues.length;
        colorAssignments.push([color, [startingRepeatIdx, endingRepeatIdx]]);
      } else {
        const pulseCopy = JSON.parse(JSON.stringify(pulse));

        // eslint-disable-next-line  no-unused-vars
        for (const _ of Array(pulse.numIterations).fill()) {
          pulseCopy.subprotocols.map((innerPulse) => {
            const { color } = innerPulse;
            let settings = innerPulse.pulseSettings;
            const startingRepeatIdx = xValues.length - 1;

            settings = {
              type: innerPulse.type,
              ...settings,
            };

            let remainingPulseCycles = innerPulse.type === "Delay" ? 1 : settings.numCycles;

            while (remainingPulseCycles > 0) {
              helper(settings, innerPulse.type);
              remainingPulseCycles--;
            }

            const endingRepeatIdx = xValues.length;
            colorAssignments.push([color, [startingRepeatIdx, endingRepeatIdx]]);
          });
        }

        pulseCopy.subprotocols = pulseCopy.subprotocols.map((loopedPulse) => {
          const settings = loopedPulse.pulseSettings;
          return {
            type: loopedPulse.type,
            ...settings,
          };
        });

        subprotocols.push(pulseCopy);
      }
    });

    // convert xValues to correct unit
    xValues.forEach((val, idx) => {
      xValues[idx] = val / TIME_CONVERSION_TO_MILLIS[state.xAxisUnitName];
    });

    commit("setRepeatColorAssignments", colorAssignments);
    commit("setSubprotocols", { subprotocols, newSubprotocolOrder });
    dispatch("handleRestDuration", {
      xValues,
      yValues,
    });
  },

  handleRestDuration({ commit, state }, { xValues, yValues }) {
    const { restDuration, timeUnit } = state.protocolEditor;
    const { xAxisTimeIdx } = state;
    const xAxisUnit = xAxisTimeIdx === 0 ? "milliseconds" : "seconds";
    let delayBlock;

    if (restDuration !== 0) {
      // find the time unit by taking rest duration unit and dividing by the graph x axis unit
      const convertedDelay =
        restDuration * (TIME_CONVERSION_TO_MILLIS[timeUnit] / TIME_CONVERSION_TO_MILLIS[xAxisUnit]);

      const lastXValue = xValues[xValues.length - 1];
      const nextXValue = lastXValue + convertedDelay;
      delayBlock = [lastXValue, nextXValue];
    }

    if (restDuration == 0) {
      delayBlock = [NaN, NaN];
    }

    commit("setDelayAxisValues", delayBlock);
    commit("setAxisValues", { xValues, yValues });
  },

  async handleNewRestDuration({ dispatch, state, commit }, time) {
    // need to grab these values before committing setRestDuration
    let { detailedSubprotocols } = state.protocolEditor;
    detailedSubprotocols = detailedSubprotocols || [];

    if (time === "") time = "0";
    await commit("setRestDuration", time);

    // commit this after committing setRestDuration
    dispatch("handleProtocolOrder", detailedSubprotocols);
  },

  async handleImportProtocol({ dispatch }, file) {
    const reader = new FileReader();

    reader.onload = async function () {
      const response = JSON.parse(reader.result);
      await dispatch("addImportedProtocol", response);
    };

    reader.onerror = function () {
      console.log(reader.onerror); // allow-log
    };

    reader.readAsText(file);
  },

  async handleExportProtocol({ state }) {
    const { protocolAssignments, protocolList } = state;
    // convert to snakecase to be interchangable with MA controller
    const protocolCopy = [];
    for (const protocol of [...protocolList]) {
      const convertedProtocol = convertProtocolCasing(protocol.protocol, _convertObjToSnakeCase);
      protocolCopy.push({ ...protocol, protocol: convertedProtocol });
    }

    const message = { protocols: protocolCopy.slice(1), protocolAssignments: {} };

    for (const wellIdx of Array(24).keys()) {
      const letter = protocolAssignments[wellIdx] ? protocolAssignments[wellIdx].letter : null;

      // asign letter to well number
      const wellNumber = twentyFourWellPlateDefinition.getWellNameFromWellIndex(wellIdx, false);
      message.protocolAssignments[wellNumber] = letter;
    }

    const textToWrite = JSON.stringify(message);
    const textFileBlob = new Blob([textToWrite], { type: "application/json" });
    // get new file name of datetime
    const currentDate = new Date();
    const datetime =
      currentDate.getFullYear() +
      "_" +
      (currentDate.getMonth() + 1) +
      "_" +
      currentDate.getDate() +
      "__" +
      currentDate.getHours() +
      currentDate.getMinutes() +
      currentDate.getSeconds();

    const fileNameToSave = "stimSettings__" + datetime;
    const downloadLink = document.createElement("a");
    downloadLink.download = fileNameToSave;
    downloadLink.innerHTML = "Download File";

    if (window.webkitURL != null) {
      downloadLink.href = window.webkitURL.createObjectURL(textFileBlob);
    } else {
      downloadLink.href = window.URL.createObjectURL(textFileBlob);
      downloadLink.style.display = "none";
      document.body.appendChild(downloadLink);
    }

    downloadLink.click();
    downloadLink.remove();
  },

  async addImportedProtocol({ commit, getters }, response) {
    const invalidImportedProtocols = [];
    // first interation only exported single protocols, not array of multiple
    const protocolsToUse = response.protocols || [{ protocol: response }];
    // reset stim studio
    await commit("resetProtocolEditor");

    for (const [idx, { protocol }] of Object.entries(protocolsToUse)) {
      // if protocol is unnamed, assign generic name with place in list, +1 to index
      protocol.name = protocol.name.length > 0 ? protocol.name : `protocol_${idx + 1}`;
      // (22/04/2023) For now with mantarray, all protocols will be exported in snake_case, including from stingray
      const convertedProtocol = convertProtocolCasing(protocol, _convertObjToCamelCase);
      const compatibleProtocol = checkPulseCompatibility(convertedProtocol);
      const invalidPulses = areValidPulses(compatibleProtocol.subprotocols);

      if (!invalidPulses) {
        await commit("setEditModeOff");
        // needs to be set to off every iteration because an action elsewhere triggers it on
        const { color, letter } = await getters["getNextProtocol"];
        const importedProtocol = { color, letter, label: protocol.name, protocol: compatibleProtocol };
        await commit("setNewProtocol", importedProtocol);
      } else {
        invalidImportedProtocols.push(protocol.name);
      }
    }

    if (invalidImportedProtocols.length > 0) {
      await commit("setInvalidImportedProtocols", invalidImportedProtocols);
    }
  },
  async addSavedPotocol({ commit, state, dispatch }) {
    const { protocolEditor, editMode, protocolList } = state;
    const { letter, color } = state.currentAssignment;

    const protocolListCopy = JSON.parse(JSON.stringify(protocolList));
    const updatedProtocol = { color, letter, label: protocolEditor.name, protocol: protocolEditor };
    if (!editMode.status) {
      commit("setNewProtocol", updatedProtocol);
    } else if (editMode.status) {
      protocolListCopy.map((protocol, idx) => {
        if (protocol.letter === editMode.letter)
          protocolListCopy[idx] = {
            ...protocol,
            label: protocolEditor.name,
            protocol: protocolEditor,
          };
      });

      await commit("setProtocolList", protocolListCopy);
      await commit("setEditModeOff");
      await dispatch("updateProtocolAssignments", updatedProtocol);
    }
  },

  updateProtocolAssignments({ state }, updatedProtocol) {
    const { protocolAssignments } = state;

    for (const assignment in protocolAssignments) {
      if (protocolAssignments[assignment].letter === updatedProtocol.letter) {
        protocolAssignments[assignment] = updatedProtocol;
      }
    }
  },

  async createProtocolMessage({ state }) {
    const message = { protocols: [], protocol_assignments: {} };

    const { protocolAssignments, stimulatorCircuitStatuses } = state;

    for (let wellIdx = 0; wellIdx < 24; wellIdx++) {
      const wellName = twentyFourWellPlateDefinition.getWellNameFromWellIndex(wellIdx, false);
      message.protocol_assignments[wellName] = null;
    }

    const uniqueProtocolIds = new Set();

    for (const well in protocolAssignments) {
      // remove open circuit wells
      if (!stimulatorCircuitStatuses.includes(Number(well))) {
        const { stimulationType, subprotocols, runUntilStopped } = protocolAssignments[well].protocol;
        const { letter } = protocolAssignments[well];

        // add protocol to list of unique protocols if it has not been entered yet
        if (!uniqueProtocolIds.has(letter)) {
          uniqueProtocolIds.add(letter);
          // this needs to be converted before sent because stim type changes independently of pulse settings
          const convertedSubprotocols = _getConvertedSettings(subprotocols, 1e3);

          const protocolModel = {
            protocol_id: letter,
            stimulation_type: stimulationType,
            run_until_stopped: runUntilStopped,
            subprotocols: convertedSubprotocols,
          };

          message.protocols.push(protocolModel);
        }

        // assign letter to well name
        const wellName = twentyFourWellPlateDefinition.getWellNameFromWellIndex(well, false);
        message.protocol_assignments[wellName] = letter;
      }
    }
    const wsProtocolMessage = JSON.stringify({ command: "set_stim_protocols", stim_info: message });
    this.state.system.socket.send(wsProtocolMessage);

    const wsMessage = JSON.stringify({ command: "set_stim_status", running: true });
    this.state.system.socket.send(wsMessage);
  },

  async stopStimulation() {
    const wsMessage = JSON.stringify({ command: "set_stim_status", running: false });
    // TODO make an action for sending WS messages
    this.state.system.socket.send(wsMessage);
  },

  async editSelectedProtocol({ commit, dispatch, state }, protocol) {
    const { label, letter, color } = protocol;
    const { timeUnit, restDuration, detailedSubprotocols, runUntilStopped } = protocol.protocol;

    state.currentAssignment = { letter, color };

    await commit("setProtocolName", label);
    await commit("setTimeUnit", timeUnit);
    await commit("setRestDuration", restDuration);
    await commit("setStopSetting", runUntilStopped);
    await dispatch("handleProtocolOrder", detailedSubprotocols);

    commit("setEditMode", protocol);
  },

  async handleProtocolEditorReset({ commit, state }) {
    const { protocolList, editMode, protocolAssignments } = state;
    const { status, label } = editMode;

    if (status) {
      protocolList.map((protocol, idx) => {
        if (protocol.label === label) protocolList.splice(idx, 1);
      });
      for (const well in protocolAssignments) {
        if (protocolAssignments[well].label === label) delete protocolAssignments[well];
      }
      await commit("setEditModeOff");
    }
    commit("resetProtocolEditor");
  },
  handleXAxisUnit({ commit, dispatch, state }, { idx, unitName }) {
    state.xAxisUnitName = unitName;
    const { xAxisValues, yAxisValues, xAxisTimeIdx } = state;

    if (idx !== xAxisTimeIdx) {
      const convertedXValues = xAxisValues.map((val) => (idx === 1 ? val * 1e-3 : val * 1e3));
      commit("setXAxisTimeIdx", idx);
      if (convertedXValues.length > 0)
        dispatch("handleRestDuration", {
          xValues: convertedXValues,
          yValues: yAxisValues,
        });
    }
  },
  async startStimConfiguration({ state, dispatch }) {
    const { barcodes } = this.state.system;
    const plateBarcode = barcodes.plateBarcode.value;
    const stimBarcode = barcodes.stimBarcode.value;
    const wellIndices = Object.keys(state.protocolAssignments);

    const wsMessage = JSON.stringify({
      command: "start_stim_checks",
      well_indices: wellIndices,
      plate_barcode: plateBarcode,
      stim_barcode: stimBarcode,
    });

    this.state.system.socket.send(wsMessage);
    dispatch("setStimStatus", STIM_STATUS.CONFIG_CHECK_IN_PROGRESS);
  },
  async onPulseMouseenter({ state }, { idx, nestedIdx }) {
    const originalPulse = state.protocolEditor.detailedSubprotocols[idx];

    if (nestedIdx >= 0) {
      // find the starting index by expanding any loops to find corresponding index in repeatColors
      const startingIdx = state.protocolEditor.detailedSubprotocols
        // filter any unnecessary indices after hovered over index
        .filter((_, i) => i < idx)
        // reduce to get index
        .reduce((acc, pulse) => {
          const val = pulse.type === "loop" ? pulse.subprotocols.length * pulse.numIterations : 1;
          return acc + val;
        }, 0);

      // loop through subprotocols x amount of times to highlight every instance in a loop
      const indicesToUse = [...Array(originalPulse.numIterations).keys()].map((i) => {
        const numSubprotocols = originalPulse.subprotocols.length;
        const idxToUse = startingIdx + nestedIdx + i * numSubprotocols;
        return state.repeatColors[idxToUse][1];
      });
      state.hoveredPulse = {
        idx,
        color: state.repeatColors[startingIdx + nestedIdx][0],
        indices: indicesToUse,
      };
    } else {
      //  find the index by expanding any loops to find corresponding index in repeatColors
      const idxToUse = state.protocolEditor.detailedSubprotocols
        .filter((_, i) => i <= idx)
        .reduce((acc, pulse, i) => {
          let val = pulse.type === "loop" ? pulse.subprotocols.length * pulse.numIterations : 1;
          if (i === 0) val = val-- < 0 ? 0 : val--;
          return acc + val;
        }, 0);

      state.hoveredPulse = {
        idx,
        indices: [state.repeatColors[idxToUse][1]],
        color: state.repeatColors[idxToUse][0],
      };
    }
  },

  checkStimulatorCircuitStatuses({ commit, dispatch }, stimulatorStatusesObj) {
    // possible status values: open, short, media, error
    const stimulatorStatuses = Object.values(stimulatorStatusesObj);

    if (stimulatorStatuses.includes("short") || stimulatorStatuses.includes("error")) {
      // set stim error status
      commit("resetState");
      dispatch("setStimStatus", STIM_STATUS.SHORT_CIRCUIT_ERROR);
    } else {
      // set the stim status that other components watch, only saves indices
      const filteredStatuses = Object.entries(stimulatorStatusesObj)
        .map(([idx, status]) => {
          return status == "open" ? +idx : undefined;
        })
        .filter((i) => i === 0 || i);

      commit("setStimulatorCircuitStatuses", filteredStatuses);
      dispatch("setStimStatus", STIM_STATUS.CONFIG_CHECK_COMPLETE);
    }
  },
  setStimStatus({ state, rootState }, status) {
    if (
      Object.keys(state.protocolAssignments).length === 0 &&
      ![STIM_STATUS.ERROR, STIM_STATUS.SHORT_CIRCUIT_ERROR, STIM_STATUS.CONFIG_CHECK_COMPLETE].includes(
        status
      ) &&
      rootState.system.statusUuid !== SYSTEM_STATUS.OFFLINE_STATE
    ) {
      state.stimStatus = STIM_STATUS.NO_PROTOCOLS_ASSIGNED;
    } else if (
      state.stimStatus === STIM_STATUS.CONFIG_CHECK_NEEDED &&
      status !== STIM_STATUS.CONFIG_CHECK_IN_PROGRESS
    ) {
      state.stimStatus = STIM_STATUS.CONFIG_CHECK_NEEDED;
    } else {
      state.stimStatus = status;
    }
  },

  async populateStimAfterOffline({ commit, state }, { stim_info }) {
    const { protocols, protocol_assignments } = stim_info;
    const protocolList = JSON.parse(JSON.stringify(state.protocolList));

    for (const protocol of protocols) {
      const protocolName = `protocol_${protocol.protocol_id}`;
      const formattedSubprotocols = _convertSubprotocolsFromFw(protocol.subprotocols[0].subprotocols);
      const detailedSubprotocols = _convertDetailedSubprotocolsFromFW(formattedSubprotocols);

      protocolList.push({
        letter: protocol.protocol_id,
        label: protocolName,
        color: COLOR_PALETTE[(protocolList.length - 1) % 26],
        protocol: {
          detailedSubprotocols,
          name: protocolName,
          restDuration: 0,
          runUntilStopped: protocol.run_until_stopped,
          stimulationType: protocol.stimulation_type,
          subprotocols: formattedSubprotocols,
          timeUnit: "milliseconds",
        },
      });
    }

    const protocolAssignments = {};
    Object.keys(protocol_assignments)
      .filter((well) => protocol_assignments[well])
      .map((well) => {
        const wellIdx = twentyFourWellPlateDefinition.getWellIndexFromWellName(well);
        protocolAssignments[wellIdx] = protocolList.find(
          (protocol) => protocol.letter == protocol_assignments[well]
        );
      });

    commit("setProtocolAssignments", protocolAssignments);
    commit("setProtocolList", protocolList);
  },
};

const _getConvertedSettings = (subprotocols, conversion) => {
  return subprotocols.map((pulse) => {
    let typeSpecificSettings = {};
    if (pulse.type === "loop") {
      typeSpecificSettings = {
        num_iterations: pulse.numIterations,
        subprotocols: _getConvertedSettings(pulse.subprotocols, conversion),
      };
    } else if (pulse.type === "Delay")
      typeSpecificSettings.duration = pulse.duration * TIME_CONVERSION_TO_MILLIS[pulse.unit] * conversion;
    else
      typeSpecificSettings = {
        num_cycles: pulse.numCycles,
        postphase_interval: Math.round(pulse.postphaseInterval * conversion), // sent in µs, also needs to be an integer value
        phase_one_duration: pulse.phaseOneDuration * conversion, // sent in µs
        phase_one_charge: pulse.phaseOneCharge * conversion, // sent in mV
      };

    if (pulse.type === "Biphasic")
      typeSpecificSettings = {
        ...typeSpecificSettings,
        interphase_interval: pulse.interphaseInterval * conversion, // sent in µs
        phase_two_charge: pulse.phaseTwoCharge * conversion, // sent in mV or µA
        phase_two_duration: pulse.phaseTwoDuration * conversion, // sent in µs
      };

    return {
      type: pulse.type,
      ...typeSpecificSettings,
    };
  });
};
