// adapted from https://stackoverflow.com/questions/53446792/nuxt-vuex-how-do-i-break-down-a-vuex-module-into-separate-files

import { STIM_STATUS } from "../stimulation/enums";
import { TextValidation } from "@/js-utils/TextValidation.js";
const TextValidationPlateBarcode = new TextValidation("plateBarcode");
// =========================================================================
// |   Following are the list of items called --todo                       |
// |   a) baseurl {contains the flask server url } {obtain from config.ini}|
// |   b) api's /startManagedAcquisition         {obtain from config.ini}|
// |            /stopManagedAcquisition                                  |
// |            /startRecording                                           |
// |            /stopRecording                                            |
// |            /startCalibration                                         |
// |                                                                       |
// |  NOTE: The python flask server as development can manage api's by     |
// |        version eg:- /v{n}/startManagedAcquisition                   |
// |        in-order to have loose-coupling and App/UI changes can be      |
// |        rollout feature without Python Flask server change its good for|
// |        to have config.ini allowing App/UI to discover api's           |
// =========================================================================

export const microsPerMilli = 1000;
/**
 * Function to progress the timeIndex
 * @return {void}
 */
// export function advancePlaybackProgression() {
//   const delayThresholdMilliseconds = this.rootState.playback.numMillisecondsToFastForwardIfDelayed;
//   const startingTimestamp = this.rootState.playback.timestampOfBeginningOfProgression;
//   const expectedDisplayTime = startingTimestamp + this.rootState.playback.xTimeIndex / microsPerMilli;
//   const currentTimestamp = performance.now();
//   let millisecondsToIncrement = this.rootState.playback.playbackProgressionTimeInterval;
//   if (currentTimestamp - expectedDisplayTime >= delayThresholdMilliseconds) {
//     millisecondsToIncrement = delayThresholdMilliseconds;
//   }
//   this.commit("incrementXTimeIndex", millisecondsToIncrement * microsPerMilli);
// }

export default {
  async validateBarcode({ commit, state, dispatch }, { type, newValue }) {
    const result = TextValidationPlateBarcode.validate(newValue, type, this.state.settings.beta2Mode);
    const isValid = result == "";
    const { stimPlayState } = this.state.stimulation;

    // stop all running processes if either barcode changes regardless of validity
    if (stimPlayState) {
      await this.dispatch("stimulation/stopStimulation");
      commit("setBarcodeWarning", true);
    }
    // require new stim configuration check if either new barcode changes
    if (isValid && state.barcodes[type].value !== newValue) {
      this.commit("stimulation/setStimStatus", STIM_STATUS.CONFIG_CHECK_NEEDED);
    }

    commit("setBarcode", { type, newValue, isValid });
  },
};
