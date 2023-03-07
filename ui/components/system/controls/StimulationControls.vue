<template>
  <div class="div__stimulation-controls-container">
    <!-- Tanner (2/1/22): Only need controls block until SVGs are made of all the buttons in this widget and they can be shaded manually when inactive-->

    <span class="span__additional-controls-header">Stimulation Controls</span>
    <div class="div__border-container">
      <svg class="svg__stimulation-active-button" height="20" width="20">
        <defs>
          <radialGradient id="greenGradient">
            <stop offset="10%" :stop-color="currentGradient[0]" />
            <stop offset="95%" :stop-color="currentGradient[1]" />
          </radialGradient>
        </defs>
        <circle cx="10" cy="10" r="10" fill="url('#greenGradient')" />
      </svg>
      <svg class="svg__stimulation-controls-loop-button" viewBox="0 0 72 72">
        <path
          d="M63.1,42,40,52.9a1.5,1.5,0,0,0-.2,2.5l4.1,2.8A23.7,23.7,0,0,1,12.4,37.1,1.4,1.4,0,0,0,11,35.7H1.6A1.4,1.4,0,0,0,.2,37.1a27.9,27.9,0,0,0,.7,5.8.4.4,0,0,0,0,.5,35.4,35.4,0,0,0,9.7,18A36.2,36.2,0,0,0,36,71.9a35.7,35.7,0,0,0,19.4-5.7L60.8,70A1.4,1.4,0,0,0,63,68.9l2.1-25.5A1.4,1.4,0,0,0,63.1,42Z"
        />
        <path
          d="M71.2,29.2a.5.5,0,0,0,0-.5A35.8,35.8,0,0,0,36.1.2,35.7,35.7,0,0,0,16.7,5.9L11.3,2.1A1.4,1.4,0,0,0,9.1,3.2L7,28.6A1.4,1.4,0,0,0,9,30L32.1,19.2a1.5,1.5,0,0,0,.2-2.5l-4.1-2.9a23.9,23.9,0,0,1,27.2,8.7A23.5,23.5,0,0,1,59.7,35a1.3,1.3,0,0,0,1.4,1.3h9.4a1.5,1.5,0,0,0,1.4-1.5A27.8,27.8,0,0,0,71.2,29.2Z"
        />
      </svg>

      <span :class="svg__stimulationControlsPlayStopButton__dynamicClass" @click="handlePlayStop">
        <div
          v-if="!playState"
          id="start-stim-button"
          v-b-popover.hover.top="startStimLabel"
          title="Start Stimulation"
        >
          <!-- this is here for testing the popover message -->
          <span id="start-popover-msg" style="display: none">{{ startStimLabel }}</span>
          <FontAwesomeIcon class="fontawesome-icon-class" :icon="['fa', 'play-circle']" />
        </div>
        <div v-if="playState" v-b-popover.hover.bottom="stopStimLabel" title="Stop Stimulation">
          <!-- this is here for testing the popover message -->
          <span id="stop-popover-msg" style="display: none">{{ stopStimLabel }}</span>
          <FontAwesomeIcon class="fontawesome-icon-class" :icon="['fa', 'stop-circle']" />
        </div>
      </span>
    </div>
    <div
      v-b-popover.hover.bottomright="'Edit account settings'"
      :title="'Settings'"
      class="div__settings-button-container"
      @click="$bvModal.show('settings-form')"
    >
      <SettingsButton />
    </div>
    <div
      v-b-popover.hover.bottom="configurationMessage"
      title="Configuration Check"
      class="div__config-check-container"
    >
      <svg
        class="svg__config-check-container"
        x="0px"
        y="0px"
        viewBox="-10 -10 100 100"
        @click="startStimConfiguration"
      >
        <path
          :class="svg__stimulationControlsConfigCheckButton__dynamicClass"
          d="M30.9,2.4c15.71,0,28.5,12.79,28.5,28.5c0,15.71-12.79,28.5-28.5,28.5S2.4,46.61,2.4,30.9
	C2.4,15.18,15.18,2.4,30.9,2.4"
        />
        <g>
          <g>
            <g>
              <g>
                <path
                  class="svg__inner-circle"
                  d="M17.26,28.81c1.14,0,2.07,0.93,2.07,2.07c0,1.14-0.93,2.07-2.07,2.07s-2.07-0.93-2.07-2.07
					C15.2,29.73,16.12,28.81,17.26,28.81 M17.26,24.81c-3.35,0-6.07,2.72-6.07,6.07c0,3.35,2.72,6.07,6.07,6.07
					c3.35,0,6.07-2.72,6.07-6.07C23.33,27.52,20.61,24.81,17.26,24.81L17.26,24.81z"
                />
              </g>
            </g>
          </g>
          <g>
            <g>
              <g>
                <path
                  class="svg__inner-circle"
                  d="M45.26,28.81c1.14,0,2.07,0.93,2.07,2.07c0,1.14-0.93,2.07-2.07,2.07s-2.07-0.93-2.07-2.07
					C43.2,29.73,44.12,28.81,45.26,28.81 M45.26,24.81c-3.35,0-6.07,2.72-6.07,6.07c0,3.35,2.72,6.07,6.07,6.07
					c3.35,0,6.07-2.72,6.07-6.07C51.33,27.52,48.61,24.81,45.26,24.81L45.26,24.81z"
                />
              </g>
            </g>
          </g>
        </g>
        <line class="svg__inner-line" x1="11.73" y1="30.87" x2="3.48" y2="30.87" />
        <line class="svg__inner-line" x1="34.8" y1="17.28" x2="21.16" y2="30.91" />
        <line class="svg__inner-line" x1="58.73" y1="30.87" x2="50.48" y2="30.87" />
      </svg>
      <span v-show="configCheckInProgress" class="span__spinner">
        <FontAwesomeIcon :style="'fill: #ececed;'" :icon="['fa', 'spinner']" pulse />
      </span>
    </div>
    <b-modal
      id="open-circuit-warning"
      size="sm"
      hide-footer
      hide-header
      hide-header-close
      :static="true"
      :no-close-on-backdrop="true"
    >
      <StatusWarningWidget :modalLabels="openCircuitLabels" @handleConfirmation="closeWarningModal" />
    </b-modal>
    <b-modal
      id="stim-24hr-warning"
      size="sm"
      hide-footer
      hide-header
      hide-header-close
      :static="true"
      :no-close-on-backdrop="true"
    >
      <StatusWarningWidget :modalLabels="timerWarningLabels" @handleConfirmation="closeTimerModal" />
    </b-modal>
    <b-modal
      id="settings-form"
      hide-footer
      hide-header
      hide-header-close
      :no-close-on-backdrop="true"
      :static="true"
    >
      <SettingsForm @close-modal="$bvModal.hide('settings-form')" />
    </b-modal>
  </div>
</template>
<script>
import { library } from "@fortawesome/fontawesome-svg-core";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import { mapState } from "vuex";
import { STIM_STATUS } from "@/store/modules/stimulation/enums";
import StatusWarningWidget from "@/components/status/StatusWarningWidget.vue";
import SettingsButton from "@/components/settings/SettingsButton.vue";
import SettingsForm from "@/components/settings/SettingsForm.vue";
import { faPlayCircle, faStopCircle, faSpinner } from "@fortawesome/free-solid-svg-icons";
import Vue from "vue";
import BootstrapVue from "bootstrap-vue";
import { VBPopover, BDropdown, BDropdownItemButton } from "bootstrap-vue";
// Note: Vue automatically prefixes the directive name with 'v-'
Vue.directive("b-popover", VBPopover);
Vue.directive("b-dropdown", BDropdown);
Vue.directive("b-dropdown-item-button", BDropdownItemButton);

Vue.use(BootstrapVue);
library.add(faPlayCircle, faStopCircle, faSpinner);

// TODO Luci, swap out PNG for SVG once folder becomes available

/**
 * @vue-data {Boolean} playState - Current play state of stimulation
 * @vue-data {Array} activeGradient - Active gradient colors for icon while stimulation is running
 * @vue-data {Array} inactiveGradient - Inactive gradient colors for icon if stimulation is stopped
 * @vue-data {Array} currentGradient - Dynamically assigned gradient based on when BE recieves start/stop request
 * @vue-event {event} handlePlayStop - Commits corresponding request to state depending on playState
 */

export default {
  name: "StimulationControls",
  components: {
    FontAwesomeIcon,
    StatusWarningWidget,
    SettingsButton,
    SettingsForm,
  },
  data() {
    return {
      playState: false,
      activeGradient: ["#19ac8a", "#24524b"],
      inactiveGradient: ["#b7b7b7", "#858585"],
      currentGradient: ["#b7b7b7", "#858585"],
      controlsBlockLabel: "Stimulation Controls are disabled until device is Calibrated",
      openCircuitLabels: {
        header: "Warning!",
        msgOne:
          "You are attempting to assign a protocol to a well that an open circuit was previously found in during the configuration check.",
        msgTwo: "Please unassign all wells labeled with an open circuit.",
        buttonNames: ["Okay"],
      },
      timerWarningLabels: {
        header: "Warning!",
        msgOne: "You have been running a stimulation for 24 hours.",
        msgTwo:
          "We strongly recommend stopping the stimulation and running another configuration check to ensure the integrity of the stimulation.",
        buttonNames: ["Continue Anyway", "Stop Stimulation"],
      },
      stim_24hrTimer: null,
      openStartDropdown: false,
    };
  },
  computed: {
    ...mapState("stimulation", [
      "protocolAssignments",
      "stimPlayState",
      "stimStatus",
      "stimulatorCircuitStatuses",
    ]),
    ...mapState("system", ["barcodes"]),
    isStartStopButtonEnabled: function () {
      if (!this.playState) {
        // if starting stim make sure initial magnetometer calibration has been completed and
        // no additional calibrations are running, stim checks have completed, there are no short or
        // open circuits, and that there are no other errors with stim lid
        return (
          this.assignedOpenCircuits.length === 0 &&
          ![
            STIM_STATUS.ERROR,
            STIM_STATUS.NO_PROTOCOLS_ASSIGNED,
            STIM_STATUS.CONFIG_CHECK_NEEDED,
            STIM_STATUS.CONFIG_CHECK_IN_PROGRESS,
            STIM_STATUS.SHORT_CIRCUIT_ERROR,
            STIM_STATUS.CALIBRATION_NEEDED,
          ].includes(this.stimStatus)
        );
      }
      // currently, stop button should always be enabled
      return true;
    },
    assignedOpenCircuits: function () {
      // filter for matching indices
      return this.stimulatorCircuitStatuses.filter((well) =>
        Object.keys(this.protocolAssignments).includes(well.toString())
      );
    },
    startStimLabel: function () {
      if (this.stimStatus === STIM_STATUS.ERROR || this.stimStatus === STIM_STATUS.SHORT_CIRCUIT_ERROR) {
        return "Cannot start a stimulation with error";
      } else if (
        this.stimStatus === STIM_STATUS.CONFIG_CHECK_NEEDED ||
        this.stimStatus === STIM_STATUS.CONFIG_CHECK_IN_PROGRESS
      ) {
        return "Configuration check needed";
      } else if (!this.barcodes.stimBarcode.valid) return "Must have a valid Stimulation Lid Barcode";
      else if (this.stimStatus === STIM_STATUS.NO_PROTOCOLS_ASSIGNED) {
        return "No protocols have been assigned";
      } else if (this.assignedOpenCircuits.length !== 0) {
        return "Cannot start stimulation with a protocol assigned to a well with an open circuit.";
      } else {
        return "Start Stimulation";
      }
    },
    stopStimLabel: function () {
      // Tanner (7/27/22): there used to be multiple values, so leaving this as a function in case more values get added in future
      return "Stop Stimulation";
    },
    svg__stimulationControlsPlayStopButton__dynamicClass: function () {
      // Tanner (2/1/22): This is only necessary so that the this button is shaded the same as the rest of
      // the stim controls buttons when the controls block is displayed. The button is
      // not actually active here. If the controls block is removed, this branch can likely be removed too.
      return this.isStartStopButtonEnabled
        ? "span__stimulation-controls-play-stop-button--enabled"
        : "span__stimulation-controls-play-stop-button--disabled";
    },
    isConfigCheckButtonEnabled: function () {
      return (
        [STIM_STATUS.CONFIG_CHECK_NEEDED, STIM_STATUS.READY].includes(this.stimStatus) &&
        this.barcodes.stimBarcode.valid
      );
    },
    svg__stimulationControlsConfigCheckButton__dynamicClass: function () {
      return this.isConfigCheckButtonEnabled
        ? "svg__stimulation-controls-config-check-button--enabled"
        : "svg__stimulation-controls-config-check-button--disabled";
    },
    configurationMessage: function () {
      if (!this.barcodes.stimBarcode.valid) {
        return "Must have a valid Stimulation Lid Barcode";
      } else if (this.stimStatus == STIM_STATUS.ERROR || this.stimStatus == STIM_STATUS.SHORT_CIRCUIT_ERROR) {
        return "Cannot run a configuration on this stim lid as a short has been detected on it";
      } else if (this.stimStatus === STIM_STATUS.NO_PROTOCOLS_ASSIGNED) {
        return "Cannot run configuration check until protocols have been assigned.";
      } else if (this.stimStatus == STIM_STATUS.CONFIG_CHECK_NEEDED) {
        return "Start configuration check";
      } else if (this.stimStatus == STIM_STATUS.CONFIG_CHECK_IN_PROGRESS) {
        return "Configuration check in progress...";
      } else if (this.stimStatus == STIM_STATUS.STIM_ACTIVE) {
        return "Cannot run a configuration check while stimulation is active.";
      } else {
        return "Configuration check complete. Click to rerun.";
      }
    },
    configCheckInProgress: function () {
      return this.stimStatus === STIM_STATUS.CONFIG_CHECK_IN_PROGRESS;
    },
  },
  watch: {
    stimPlayState: function () {
      this.currentGradient = this.stimPlayState ? this.activeGradient : this.inactiveGradient;
      this.playState = this.stimPlayState;
    },
    assignedOpenCircuits: function (newVal, oldVal) {
      if (this.stimStatus !== STIM_STATUS.CONFIG_CHECK_COMPLETE && newVal.length > oldVal.length)
        this.$bvModal.show("open-circuit-warning");
    },
  },
  mounted() {
    document.addEventListener("click", () => {
      this.openStartDropdown = false;
    });
  },
  methods: {
    async handlePlayStop(e) {
      e.preventDefault();
      if (this.isStartStopButtonEnabled) {
        if (this.playState) {
          this.$store.dispatch(`stimulation/stopStimulation`);
          clearTimeout(this.stim_24hrTimer); // clear 24 hour timer for next stimulation
        } else {
          await this.$store.dispatch(`stimulation/createProtocolMessage`);
          this.start_24hrTimer();
        }
      }
    },
    async startStimConfiguration() {
      if (this.isConfigCheckButtonEnabled && !this.configCheckInProgress)
        this.$store.dispatch(`stimulation/startStimConfiguration`);
    },
    async closeWarningModal() {
      this.$bvModal.hide("open-circuit-warning");
    },
    async closeTimerModal(idx) {
      this.$bvModal.hide("stim-24hr-warning");
      if (idx === 1) {
        await this.$store.dispatch(`stimulation/stopStimulation`);
        clearTimeout(this.start_24hrTimer);
      } else this.start_24hrTimer(); // start new timer
    },
    async start_24hrTimer() {
      this.stim_24hrTimer = setTimeout(() => {
        this.$bvModal.show("stim-24hr-warning");
      }, 24 * 60 * 60e3);
    },
  },
};
</script>
<style>
body {
  user-select: none;
}

.div__settings-button-container {
  top: 33px;
  left: 0px;
  width: 0px;
  position: relative;
  background-color: #000000;
  font-family: Muli;
  font-weight: normal;
  font-style: normal;
  text-decoration: none;
  text-align: center;
  color: #2f2f2f;
  fill: #2f2f2f;
}

.div__stimulation-controls-container {
  position: relative;
  background: black;
  height: 85px;
  width: 287px;
  font-family: Muli;
  padding-left: 20px;
  top: 0px;
  left: 0px;
  overflow: hidden;
}

.div__controls-block {
  position: absolute;
  z-index: 999;
  background: black;
  opacity: 0.7;
  height: 85px;
  width: 287px;
  padding-left: 20px;
  top: 0px;
  left: 0px;
}

.span__additional-controls-header {
  color: rgb(255, 255, 255);
  position: absolute;
  font-size: 16px;
}

.div__border-container {
  position: absolute;
  border: 3px solid rgb(17, 17, 17);
  height: 40px;
  width: 110px;
  top: 35px;
  left: 100px;
  display: grid;
  grid-template-columns: repeat(25%, 4);
  align-items: center;
  justify-items: center;
  padding: 5px;
}

.span__stimulation-controls-play-stop-button--disabled {
  position: relative;
  color: #2f2f2f;
  font-size: 23px;
  grid-column: 4;
}

.b-dropdown__container {
  position: relative;
  grid-column: 4;
  height: 29px;
  width: 20px;
}
.dropdown-item {
  font-size: 13px;
  padding: 5px 9px;
}

.dropdown-item:focus {
  background: gray;
}

.dropdown-menu {
  position: fixed;
  padding: 0;
  min-width: 0px;
  display: flex;
  flex-direction: column;
  height: 63px;
  top: 295px;
  left: 182px;
  border: none;
}

.span__stimulation-controls-play-stop-button--enabled {
  position: relative;
  color: #b7b7b7;
  font-size: 22px;
  grid-column: 4;
}

.span__stimulation-controls-play-stop-button--enabled:hover {
  color: #ffffff;
  cursor: pointer;
}

.svg__stimulation-controls-loop-button {
  position: relative;
  fill: #b7b7b7;
  height: 20px;
  width: 20px;
  grid-column: 3/4;
}

.svg__stimulation-active-button {
  position: relative;
  color: #b7b7b7;
  grid-column: 2/3;
}

.img__temp-icon {
  cursor: pointer;
  position: relative;
  height: 55px;
}

.img__waveform-icon {
  position: absolute;
  top: 27px;
  height: 60px;
  left: 2px;
}

.fontawesome-icon-class {
  height: 20px;
  width: 20px;
}

.span__spinner {
  position: absolute;
  font-size: 34px;
  right: 17.5px;
  bottom: 15px;
  width: 45px;
  color: #fff;
  padding-left: 5px;
  background-color: #000;
  opacity: 0.85;
}

.svg__config-check-container {
  height: 67px;
  left: 20px;
}

.div__config-check-container {
  top: 26px;
  left: 60px;
  position: absolute;
}

.svg__waveform-icon {
  fill: #b7b7b7;
}

.svg__waveform-container {
  height: 44px;
  top: 32px;
  right: 4px;
  position: relative;
}

.svg__stimulation-controls-config-check-button--disabled {
  fill: #2f2f2f;
  stroke: #2f2f2f;
  position: relative;
  stroke-width: 6px;
}

.svg__stimulation-controls-config-check-button--enabled {
  fill: #b7b7b7;
  stroke: #b7b7b7;
  position: relative;
  stroke-width: 6px;
  cursor: pointer;
}

.svg__stimulation-controls-config-check-button--enabled:hover {
  fill: #ffffff;
  stroke: #ffffff;
}

.svg__inner-line {
  stroke: black;
  stroke-width: 6;
  fill: none;
}

.svg__inner-circle {
  stroke: black;
  stroke-width: 8;
  fill: none;
}

#open-circuit-warning,
#stim-24hr-warning {
  position: fixed;
  margin: 5% auto;
  top: 15%;
  left: 0;
  right: 0;
}
</style>
