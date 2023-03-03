<template>
  <div>
    <StimulationStudio :style="'top: 45px;'" />
    <button class="update-button" @click="update_protocolList">Update protocol list</button>
    <button class="update-button" :style="'top: 300px;'" @click="create_message">Create message</button>
    <button class="update-button" :style="'top: 500px;'" @click="enable_controls">Enable buttons</button>
    <button class="update-button" :style="'top: 700px;'" @click="mock_config_check">Mock config check</button>
  </div>
</template>
<script>
import StimulationStudio from "@/components/stimulation/StimulationStudio.vue";
import { mapMutations, mapActions } from "vuex";
import { STIM_STATUS } from "@/store/modules/stimulation/enums";
// import { StimulationStudio, StimulationControls } from "@/dist/mantarray.common";

export default {
  components: {
    StimulationStudio,
  },
  layout: "default",
  methods: {
    ...mapMutations("stimulation", ["setNewProtocol", "resetState", "setStimStatus"]),
    ...mapActions("stimulation", ["createProtocolMessage"]),
    async update_protocolList() {
      const test_protocol = {
        label: "mock_protocol",
        letter: "A",
        color: "#4ca0af",
        protocol: {
          name: "mock",
          stimulationType: "C",
          runUntilStopped: false,
          restDuration: 0,
          timeUnit: "seconds",
          subprotocols: [
            {
              type: "Biphasic",
              phaseOneDuration: 3,
              phaseOneCharge: 40,
              interphaseInterval: 1,
              phaseTwoDuration: 3,
              phaseTwoCharge: -40,
              postphaseInterval: 1,
              num_cycles: 5,
            },
            {
              type: "Delay",
              duration: 50,
              unit: "milliseconds",
            },
            {
              type: "Biphasic",
              phaseOneDuration: 4,
              phaseOneCharge: 10,
              interphaseInterval: 1,
              phaseTwoDuration: 4,
              phaseTwoCharge: -10,
              postphaseInterval: 1,
              num_cycles: 5,
            },
          ],
          detailedSubprotocols: [
            {
              type: "Biphasic",
              src: "/Biphasic.png",
              nested_protocols: [],
              color: "bb9e69",
              pulse_settings: {
                phaseOneDuration: 3,
                phaseOneCharge: 40,
                interphaseInterval: 1,
                phaseTwoDuration: 3,
                phaseTwoCharge: -40,
                postphaseInterval: 1,
                total_active_duration: { duration: 50, unit: "milliseconds" },
                num_cycles: 1,
                frequency: 1,
              },
            },
            {
              type: "Delay",
              src: "/Delay.png",
              nested_protocols: [],
              color: "70f30",
              pulse_settings: {
                duration: 50,
                unit: "milliseconds",
              },
            },
            {
              type: "Biphasic",
              src: "/Biphasic.png",
              nested_protocols: [],
              color: "e9584b",
              pulse_settings: {
                phaseOneDuration: 4,
                phaseOneCharge: 10,
                interphaseInterval: 1,
                phaseTwoDuration: 4,
                phaseTwoCharge: -10,
                postphaseInterval: 1,
                total_active_duration: { duration: 50, unit: "milliseconds" },
                num_cycles: 1,
                frequency: 1,
              },
            },
          ],
        },
      };
      const test_protocol_2 = {
        label: "mock_protocol_2",
        letter: "B",
        color: "#578844",
        protocol: {
          name: "mock_protocol_2",
          stimulationType: "V",
          runUntilStopped: true,
          restDuration: 1,
          timeUnit: "seconds",
          subprotocols: [
            {
              type: "Biphasic",
              phaseOneDuration: 5,
              phaseOneCharge: 200,
              interphaseInterval: 0,
              phaseTwoDuration: 5,
              phaseTwoCharge: -200,
              postphaseInterval: 0,
              num_cycles: 1,
            },
            {
              type: "Delay",
              duration: 1,
              unit: "seconds",
            },
          ],
          detailedSubprotocols: [
            {
              type: "Biphasic",
              src: "/Biphasic.png",
              nested_protocols: [],
              color: "5391fa",
              pulse_settings: {
                phaseOneDuration: 5,
                phaseOneCharge: 200,
                interphaseInterval: 0,
                phaseTwoDuration: 5,
                phaseTwoCharge: -200,
                postphaseInterval: 0,
                total_active_duration: { duration: 1, unit: "seconds" },
                num_cycles: 1,
                frequency: 2,
              },
            },
          ],
        },
      };
      this.setNewProtocol(test_protocol);
      this.setNewProtocol(test_protocol_2);

      this.resetState();
    },
    create_message() {
      this.createProtocolMessage();
    },
    enable_controls() {
      this.$store.dispatch("playback/validateBarcode", {
        type: "stimBarcode",
        new_value: "MS2022001000",
      });
      // this.$store.commit("playback/set_playback_state", playback_module.ENUMS.PLAYBACK_STATES.CALIBRATED);
    },
    mock_config_check() {
      //   this.setStimStatus(STIM_STATUS.CONFIG_CHECK_IN_PROGRESS);
      this.setStimStatus(STIM_STATUS.SHORT_CIRCUIT_ERROR);
    },
  },
};
</script>
<style scoped>
.update-button {
  position: absolute;
  top: 100px;
  left: 1740px;
  border: none;
  color: white;
  padding: 15px 32px;
  text-align: center;
  text-decoration: none;
  display: inline-block;
  font-size: 16px;
  margin: 4px 2px;
  cursor: pointer;
  background-color: #4ca0af;
  z-index: 999;
}
</style>
