import { WellTitle as LabwareDefinition } from "@/js_utils/labware_calculations.js";
const twentyFourWellPlateDefinition = new LabwareDefinition(4, 6);
// import { call_axios_post_from_vuex } from "../../../js_utils/axios_helpers";
import { STIM_STATUS, TIME_CONVERSION_TO_MILLIS } from "./enums";

export default {
  handleSelectedWells({ commit }, wells) {
    const well_values = [];

    wells.filter((well, idx) => {
      if (well) well_values.push(idx);
    });

    commit("setSelectedWells", well_values);
  },

  async handleProtocolOrder({ commit, dispatch, state }, newSubprotocolOrder) {
    const xValues = [0];
    const yValues = [0];
    const color_assignments = [];
    const subprotocols = [];
    const get_last = (array) => array[array.length - 1];
    const helper = (setting, type) => {
      let components_to_add = [];
      if (type === "Delay") {
        components_to_add = {
          x: [setting.duration * TIME_CONVERSION_TO_MILLIS[setting.unit]],
          y: [0],
        };
      } else {
        // Add values for phase 1
        components_to_add = {
          x: [setting.phaseOneDuration],
          y: [setting.phaseOneCharge],
        };
        // If biphasic, handle remaining pulse components
        if (setting.phaseTwoDuration != null) {
          // Add values for interphase interval
          components_to_add.x.push(setting.interphaseInterval);
          components_to_add.y.push(0);
          // Add values for phase 2
          components_to_add.x.push(setting.phaseTwoDuration);
          components_to_add.y.push(setting.phaseTwoCharge);
        }
        // Add values for delay
        components_to_add.x.push(setting.postphaseInterval);
        components_to_add.y.push(0);
      }
      const num_components_to_add = components_to_add.x.length;
      // add components until all are added or the total active duration is reached
      for (let i = 0; i < num_components_to_add; i++) {
        const component_duration = components_to_add.x[i];

        xValues.push(get_last(xValues), component_duration + get_last(xValues));
        yValues.push(components_to_add.y[i], components_to_add.y[i]);
      }
      // set final value to zero in case the pulse was cut off in the middle of either phase
      xValues.push(get_last(xValues));
      yValues.push(0);
    };

    await newSubprotocolOrder.map(async (pulse) => {
      const { color } = pulse;
      let settings = pulse.pulse_settings;

      const starting_repeat_idx = xValues.length - 1;

      settings = {
        type: pulse.type,
        ...settings,
      };

      subprotocols.push(settings);

      // num_cycles defaults to 0 and delay will never update unless run through once
      let remaining_pulse_cycles = pulse.type === "Delay" ? 1 : settings.num_cycles;

      while (remaining_pulse_cycles > 0) {
        helper(settings, pulse.type);
        remaining_pulse_cycles--;
      }

      const ending_repeat_idx = xValues.length;
      color_assignments.push([color, [starting_repeat_idx, ending_repeat_idx]]);
    });

    // convert xValues to correct unit
    xValues.forEach((val, idx) => {
      xValues[idx] = val / TIME_CONVERSION_TO_MILLIS[state.xAxisUnitName];
    });

    commit("setRepeatColorAssignments", color_assignments);
    commit("setSubprotocols", { subprotocols, newSubprotocolOrder });
    dispatch("handleRestDuration", {
      xValues,
      yValues,
    });
  },

  handleRestDuration({ commit, state }, { xValues, yValues }) {
    const { restDuration, timeUnit } = state.protocolEditor;
    const { xAxisTimeIdx } = state;
    const x_axis_unit = xAxisTimeIdx === 0 ? "milliseconds" : "seconds";
    let delay_block;

    if (restDuration !== 0) {
      // find the time unit by taking rest duration unit and dividing by the graph x axis unit
      const converted_delay =
        restDuration * (TIME_CONVERSION_TO_MILLIS[timeUnit] / TIME_CONVERSION_TO_MILLIS[x_axis_unit]);

      const last_x_value = xValues[xValues.length - 1];
      const next_x_value = last_x_value + converted_delay;
      delay_block = [last_x_value, next_x_value];
    }

    if (restDuration == 0) {
      delay_block = [NaN, NaN];
    }

    commit("setDelayAxisValues", delay_block);
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
    const protocol_copy = JSON.parse(JSON.stringify(protocolList));
    const message = { protocols: protocol_copy.slice(1), protocolAssignments: {} };

    for (const well_idx of Array(24).keys()) {
      const letter = protocolAssignments[well_idx] ? protocolAssignments[well_idx].letter : null;

      // asign letter to well number
      const well_number = twentyFourWellPlateDefinition.get_well_name_from_well_index(well_idx, false);
      message.protocolAssignments[well_number] = letter;
    }

    const text_to_write = JSON.stringify(message);
    const text_file_blob = new Blob([text_to_write], { type: "application/json" });
    // get new file name of datetime
    const current_date = new Date();
    const datetime =
      current_date.getFullYear() +
      "_" +
      (current_date.getMonth() + 1) +
      "_" +
      current_date.getDate() +
      "__" +
      current_date.getHours() +
      current_date.getMinutes() +
      current_date.getSeconds();

    const file_name_to_save = "stim_settings__" + datetime;
    const download_link = document.createElement("a");
    download_link.download = file_name_to_save;
    download_link.innerHTML = "Download File";

    if (window.webkitURL != null) {
      download_link.href = window.webkitURL.createObjectURL(text_file_blob);
    } else {
      download_link.href = window.URL.createObjectURL(text_file_blob);
      download_link.style.display = "none";
      document.body.appendChild(download_link);
    }

    download_link.click();
    download_link.remove();
  },

  async addImportedProtocol({ commit, getters }, { protocols }) {
    for (const { protocol } of protocols) {
      // needs to be set to off every iteration because an action elsewhere triggers it on
      await commit("setEditModeOff");
      const { color, letter } = await getters["getNextProtocol"];
      const imported_protocol = { color, letter, label: protocol.name, protocol };
      await commit("setImportedProtocol", imported_protocol);
    }
  },
  async addSavedPotocol({ commit, state, dispatch }) {
    const { protocolEditor, editMode, protocolList } = state;
    const { letter, color } = state.currentAssignment;
    const updated_protocol = { color, letter, label: protocolEditor.name, protocol: protocolEditor };

    if (!editMode.status) {
      commit("setNewProtocol", updated_protocol);
    } else if (editMode.status) {
      protocolList.map((protocol, idx) => {
        if (protocol.letter === editMode.letter)
          protocolList[idx] = {
            ...protocol,
            label: protocolEditor.name,
            protocol: protocolEditor,
          };
      });

      await commit("setEditModeOff");
      await dispatch("updateProtocolAssignments", updated_protocol);
    }
  },

  updateProtocolAssignments({ state }, updated_protocol) {
    const { protocolAssignments } = state;

    for (const assignment in protocolAssignments) {
      if (protocolAssignments[assignment].letter === updated_protocol.letter) {
        protocolAssignments[assignment] = updated_protocol;
      }
    }
  },

  async createProtocolMessage({ commit, state }) {
    const status = true;
    const message = { protocols: [], protocolAssignments: {} };

    const { protocolAssignments } = state;
    const { stimulatorCircuitStatuses } = this.state.data;

    for (let well_idx = 0; well_idx < 24; well_idx++) {
      const well_name = twentyFourWellPlateDefinition.get_well_name_from_well_index(well_idx, false);
      message.protocolAssignments[well_name] = null;
    }

    const unique_protocol_ids = new Set();
    for (const well in protocolAssignments) {
      // remove open circuit wells
      if (!stimulatorCircuitStatuses.includes(Number(well))) {
        const { stimulationType, subprotocols, runUntilStopped } = protocolAssignments[well].protocol;

        const { letter } = protocolAssignments[well];

        // add protocol to list of unique protocols if it has not been entered yet
        if (!unique_protocol_ids.has(letter)) {
          unique_protocol_ids.add(letter);
          // this needs to be converted before sent because stim type changes independently of pulse settings
          const convertedSubprotocols = await _getConvertedSettings(subprotocols, stimulationType);
          const protocol_model = {
            protocol_id: letter,
            stimulationType,
            runUntilStopped,
            subprotocols: convertedSubprotocols,
          };

          message.protocols.push(protocol_model);
        }
        // assign letter to well number
        const well_number = twentyFourWellPlateDefinition.get_well_name_from_well_index(well, false);
        message.protocolAssignments[well_number] = letter;
      }
    }

    // TODO
  },

  async stopStimulation({ commit }) {
    // TODO
  },

  async editSelectedProtocol({ commit, dispatch, state }, protocol) {
    const { label, letter, color } = protocol;
    const {
      stimulationType,
      timeUnit,
      restDuration,
      detailedSubprotocols,
      runUntilStopped,
    } = protocol.protocol;

    state.currentAssignment = { letter, color };

    await commit("setProtocolName", label);
    await commit("setStimulationType", stimulationType);
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
  handleXAxisUnit({ commit, dispatch, state }, { idx, unit_name }) {
    state.xAxisUnitName = unit_name;
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
  async startStimConfiguration({ commit, state }) {
    const url = `/start_stim_checks`;
    const well_indices = Object.keys(state.protocolAssignments);

    // TODO
  },
  async onPulseMouseenter({ state }, idx) {
    const hoveredPulse = state.repeatColors[idx];

    state.hoveredPulse = {
      idx,
      indices: hoveredPulse[1],
      color: hoveredPulse[0],
    };
  },

  checkStimulatorCircuitStatuses({ commit }, stimulatorStatusesObj) {
    // possible status values: open, short, media, error
    const stimulatorStatuses = Object.values(stimulatorStatusesObj);

    if (stimulatorStatuses.includes("short") || stimulatorStatuses.includes("error")) {
      // set stim error status
      commit("resetState");
      commit("setStimStatus", STIM_STATUS.SHORT_CIRCUIT_ERROR);
    } else {
      // set the stim status that other components watch, only saves indices
      const filtered_statuses = Object.entries(stimulatorStatusesObj)
        .map(([idx, status]) => {
          return status == "open" ? +idx : undefined;
        })
        .filter((i) => i === 0 || i);

      commit("setStimulatorCircuitStatuses", filtered_statuses);
      commit("setStimStatus", STIM_STATUS.CONFIG_CHECK_COMPLETE);
    }
  },
};

const _getConvertedSettings = async (subprotocols, stim_type) => {
  const milliToMicro = 1e3;
  const charge_conversion = { C: 1000, V: 1 };
  const conversion = charge_conversion[stim_type];

  return subprotocols.map((pulse) => {
    let typeSpecificSettings = {};
    if (pulse.type === "Delay")
      typeSpecificSettings.duration = pulse.duration * TIME_CONVERSION_TO_MILLIS[pulse.unit] * milliToMicro;
    else
      typeSpecificSettings = {
        num_cycles: pulse.num_cycles,
        postphaseInterval: Math.round(pulse.postphaseInterval * milliToMicro), // sent in µs, also needs to be an integer value
        phaseOneDuration: pulse.phaseOneDuration * milliToMicro, // sent in µs
        phaseOneCharge: pulse.phaseOneCharge * conversion, // sent in mV
      };

    if (pulse.type === "Biphasic")
      typeSpecificSettings = {
        ...typeSpecificSettings,
        interphaseInterval: pulse.interphaseInterval * milliToMicro, // sent in µs
        phaseTwoCharge: pulse.phaseTwoCharge * conversion, // sent in mV or µA
        phaseTwoDuration: pulse.phaseTwoDuration * milliToMicro, // sent in µs
      };

    return {
      type: pulse.type,
      ...typeSpecificSettings,
    };
  });
};
