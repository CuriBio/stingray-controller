// adapted from https://stackoverflow.com/questions/53446792/nuxt-vuex-how-do-i-break-down-a-vuex-module-into-separate-files
// import { callAxiosGetFromVuex } from "@/js-utils/axiosHelpers.js";

/**
 * Function to Ping Flask server to get systemStatus
 * @return {void}
 */
export async function pingSystemStatus() {
  // const params = { currentVuexStatusUuid: this.state.statusUuid };
  // if (this.state.statusUuid === STATUS.MESSAGE.LIVE_VIEW_ACTIVE) {
  //   const currentTimeIndex = this.rootState.playback.xTimeIndex;
  //   params.currentlyDisplayedTimeIndex = currentTimeIndex;
  // }
  // const url = "http://localhost:4567/systemStatus";
  // const result = await callAxiosGetFromVuex(url, this, params);
  // if (result.status == 200) {
  //   const data = result.data;
  //   const statusUuid = data.uiStatusCode;
  //   const simulationMode = data.inSimulationMode;
  //   this.commit("setSimulationStatus", simulationMode);
  //   if (this.state.ignoreNextSystemStatusIfMatchingThisStatus !== statusUuid) {
  //     if (statusUuid != this.state.statusUuid) {
  //       this.commit("setStatusUuid", statusUuid);
  //       if (statusUuid == STATUS.MESSAGE.CALIBRATION_NEEDED) {
  //         this.dispatch(
  //           "playback/transitionPlaybackState",
  //           PLAYBACK_ENUMS.PLAYBACK_STATES.CALIBRATION_NEEDED,
  //           { root: true }
  //         );
  //       } else if (statusUuid == STATUS.MESSAGE.CALIBRATED) {
  //         // awaiting to ensure playback state gets changed to this calibrated state before enabling stim controls
  //         await this.dispatch(
  //           "playback/transitionPlaybackState",
  //           PLAYBACK_ENUMS.PLAYBACK_STATES.CALIBRATED,
  //           {
  //             root: true,
  //           }
  //         );
  //         await this.commit("stimulation/setStimStatus",STIM_STATUS.CONFIG_CHECK_NEEDED, { root: true });
  //         this.commit("playback/setEnableStimControls", true, { root: true });
  //       } else if (statusUuid == STATUS.MESSAGE.LIVE_VIEW_ACTIVE) {
  //         this.dispatch(
  //           "playback/transitionPlaybackState",
  //           PLAYBACK_ENUMS.PLAYBACK_STATES.LIVE_VIEW_ACTIVE,
  //           { root: true }
  //         );
  //       }
  //     }
  //   }
  //   this.commit("stimulation/setStimPlayState", data.isStimulating, { root: true });
  // }
  // this.commit("flask/ignoreNextSystemStatusIfMatchingStatus", null, {
  //   root: true,
  // }); // reset back to NULL now that a full call to /systemStatus has been processed
}

export default {
  async startStatusPinging(context) {
    // if (context.state.statusPingIntervald === null) {
    //   const boundPingSystemStatus = pingSystemStatus.bind(context);
    //   await boundPingSystemStatus(); // call the function immediately, instead of waiting for the first interval to elapse
    // const newIntervalId = setInterval(boundPingSystemStatus, 1000);
    // context.commit("setStatusPingIntervald", newIntervalId);
    // }
  },
};
