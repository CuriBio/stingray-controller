// adapted from https://stackoverflow.com/questions/53446792/nuxt-vuex-how-do-i-break-down-a-vuex-module-into-separate-files

import { STIM_STATUS } from "../stimulation/enums";
import { TextValidation } from "@/js_utils/text_validation.js";
const TextValidation_plateBarcode = new TextValidation("plateBarcode");
// =========================================================================
// |   Following are the list of items called --todo                       |
// |   a) baseurl {contains the flask server url } {obtain from config.ini}|
// |   b) api's /start_managed_acquisition         {obtain from config.ini}|
// |            /stop_managed_acquisition                                  |
// |            /start_recording                                           |
// |            /stop_recording                                            |
// |            /start_calibration                                         |
// |                                                                       |
// |  NOTE: The python flask server as development can manage api's by     |
// |        version eg:- /v{n}/start_managed_acquisition                   |
// |        in-order to have loose-coupling and App/UI changes can be      |
// |        rollout feature without Python Flask server change its good for|
// |        to have config.ini allowing App/UI to discover api's           |
// =========================================================================

export const micros_per_milli = 1000;
/**
 * Function to progress the time_index
 * @return {void}
 */
// export function advance_playback_progression() {
//   const delay_threshold_milliseconds = this.rootState.playback.num_milliseconds_to_fast_forward_if_delayed;
//   const starting_timestamp = this.rootState.playback.timestamp_of_beginning_of_progression;
//   const expected_display_time = starting_timestamp + this.rootState.playback.xTimeIndex / micros_per_milli;
//   const current_timestamp = performance.now();
//   let milliseconds_to_increment = this.rootState.playback.playback_progression_time_interval;
//   if (current_timestamp - expected_display_time >= delay_threshold_milliseconds) {
//     milliseconds_to_increment = delay_threshold_milliseconds;
//   }
//   this.commit("increment_xTimeIndex", milliseconds_to_increment * micros_per_milli);
// }

export default {
  async validateBarcode({ commit, state, dispatch }, { type, new_value }) {
    const result = TextValidation_plateBarcode.validate(new_value, type, this.state.settings.beta2Mode);
    const is_valid = result == "";
    const { stimPlayState } = this.state.stimulation;

    // stop all running processes if either barcode changes regardless of validity
    if (stimPlayState) {
      await this.dispatch("stimulation/stopStimulation");
      commit("setBarcodeWarning", true);
    }
    // require new stim configuration check if either new barcode changes
    if (is_valid && state.barcodes[type].value !== new_value) {
      this.commit("stimulation/setStimStatus", STIM_STATUS.CONFIG_CHECK_NEEDED);
    }

    commit("setBarcode", { type, new_value, is_valid });
  },
};
