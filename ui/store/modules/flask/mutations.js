// adapted from https://stackoverflow.com/questions/53446792/nuxt-vuex-how-do-i-break-down-a-vuex-module-into-separate-files
import { STATUS } from "./enums";

export default {
  setStatusPingIntervald(state, new_id) {
    state.statusPingIntervald = new_id;
  },
  stopStatusPinging(state) {
    if (state.statusPingIntervald !== null) {
      clearInterval(state.statusPingIntervald);
      state.statusPingIntervald = null;
    }
  },
  setStatusUuid(state, new_id) {
    if (state.statusUuid !== STATUS.MESSAGE.ERROR) {
      state.statusUuid = new_id;
    }
  },
  setSimulationStatus(state, new_id) {
    state.simulation_mode = new_id;
  },
  setBarcodeManualMode(state, new_value) {
    state.barcodeManualMode = new_value;
  },
  ignore_next_system_status_if_matching_status(state, new_status) {
    state.ignoreNextSystemStatusIfMatchingThisStatus = new_status;
  },
};
