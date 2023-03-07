<template>
  <div>
    <StimulationStudio :style="'top: 45px;'" />
    <button class="update-button" @click="updateProtocolList">Update protocol list</button>
    <button class="update-button" :style="'top: 300px;'" @click="createMessage">Create message</button>
    <button class="update-button" :style="'top: 500px;'" @click="enableControls">Enable buttons</button>
    <button class="update-button" :style="'top: 700px;'" @click="mockConfigCheck">Mock config check</button>
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
    async updateProtocolList() {
      const testProtocol = {
        label: "mockProtocol",
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
              numCycles: 5,
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
              numCycles: 5,
            },
          ],
          detailedSubprotocols: [
            {
              type: "Biphasic",
              src: "/Biphasic.png",
              nestedProtocols: [],
              color: "bb9e69",
              pulseSettings: {
                phaseOneDuration: 3,
                phaseOneCharge: 40,
                interphaseInterval: 1,
                phaseTwoDuration: 3,
                phaseTwoCharge: -40,
                postphaseInterval: 1,
                totalActiveDuration: { duration: 50, unit: "milliseconds" },
                numCycles: 1,
                frequency: 1,
              },
            },
            {
              type: "Delay",
              src: "/Delay.png",
              nestedProtocols: [],
              color: "70f30",
              pulseSettings: {
                duration: 50,
                unit: "milliseconds",
              },
            },
            {
              type: "Biphasic",
              src: "/Biphasic.png",
              nestedProtocols: [],
              color: "e9584b",
              pulseSettings: {
                phaseOneDuration: 4,
                phaseOneCharge: 10,
                interphaseInterval: 1,
                phaseTwoDuration: 4,
                phaseTwoCharge: -10,
                postphaseInterval: 1,
                totalActiveDuration: { duration: 50, unit: "milliseconds" },
                numCycles: 1,
                frequency: 1,
              },
            },
          ],
        },
      };
      const testProtocol_2 = {
        label: "mockProtocol_2",
        letter: "B",
        color: "#578844",
        protocol: {
          name: "mockProtocol_2",
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
              numCycles: 1,
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
              nestedProtocols: [],
              color: "5391fa",
              pulseSettings: {
                phaseOneDuration: 5,
                phaseOneCharge: 200,
                interphaseInterval: 0,
                phaseTwoDuration: 5,
                phaseTwoCharge: -200,
                postphaseInterval: 0,
                totalActiveDuration: { duration: 1, unit: "seconds" },
                numCycles: 1,
                frequency: 2,
              },
            },
          ],
        },
      };
      this.setNewProtocol(testProtocol);
      this.setNewProtocol(testProtocol_2);

      this.resetState();
    },
    createMessage() {
      this.createProtocolMessage();
    },
    enableControls() {
      this.$store.dispatch("system/validateBarcode", {
        type: "stimBarcode",
        newValue: "MS2022001000",
      });
    },
    mockConfigCheck() {
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
