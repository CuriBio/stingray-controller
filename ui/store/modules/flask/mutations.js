// adapted from https://stackoverflow.com/questions/53446792/nuxt-vuex-how-do-i-break-down-a-vuex-module-into-separate-files
import { STATUS } from "./enums";

export default {
  setStatusPingIntervald(state, newId) {
    state.statusPingIntervald = newId;
  },
  stopStatusPinging(state) {
    if (state.statusPingIntervald !== null) {
      clearInterval(state.statusPingIntervald);
      state.statusPingIntervald = null;
    }
  },
  setStatusUuid(state, newId) {
    if (state.statusUuid !== STATUS.MESSAGE.ERROR) {
      state.statusUuid = newId;
    }
  },
  setSimulationStatus(state, newId) {
    state.simulationMode = newId;
  },
  setBarcodeManualMode(state, newValue) {
    state.barcodeManualMode = newValue;
  },
  ignoreNextSystemStatusIfMatchingStatus(state, newStatus) {
    state.ignoreNextSystemStatusIfMatchingThisStatus = newStatus;
  },
};
