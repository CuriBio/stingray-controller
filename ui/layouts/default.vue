<template>
  <div>
    <div class="div__sidebar">
      <div class="div__sidebar-page-divider" />
      <div class="div__accordian-container" role="tablist">
        <div class="div__plate-barcode-container">
          <BarcodeViewer />
        </div>
        <div class="div__stim-barcode-container">
          <BarcodeViewer :barcode_type="'stim_barcode'" />
        </div>
        <div class="div__stim-status-container">
          <StatusBar :stim_specific="true" @send_confirmation="send_confirmation" />
        </div>
        <div class="div__stimulation_controls-controls-icon-container">
          <StimulationControls />
        </div>
        <div class="div__simulation-mode-container">
          <SimulationMode />
        </div>
        <span class="span__copyright"
          >&copy;{{ current_year }} Curi Bio. All Rights Reserved. Version:
          {{ package_version }}
        </span>
      </div>
    </div>
    <div class="div__top-bar-above-waveforms"></div>
    <div class="div__nuxt-page">
      <nuxt />
    </div>
  </div>
</template>
<script>
import Vue from "vue";

import BarcodeViewer from "@/components/playback/controls/BarcodeViewer";
import StimulationControls from "@/components/playback/controls/StimulationControls";
import StatusBar from "@/components/status/StatusBar";
import SimulationMode from "@/components/status/SimulationMode";

import { mapState } from "vuex";
import { VBPopover, VBToggle } from "bootstrap-vue";

// Note: Vue automatically prefixes the directive name with 'v-'
Vue.directive("b-popover", VBPopover);
Vue.directive("b-toggle", VBToggle);

export default {
  components: {
    BarcodeViewer,
    StatusBar,
    SimulationMode,
    StimulationControls
  },
  data: function() {
    return {
      package_version: "",
      current_year: "2023", // TODO look into better ways of handling this. Not sure if just using the system's current year is the best approach
      beta_2_mode: process.env.SPECTRON || undefined,
      pulse3d_versions: undefined
    };
  },
  computed: {
    ...mapState("settings", [
      "user_accounts",
      "active_user_index",
      "active_customer_id",
      "allow_sw_update_install",
      "recordings_list",
      "root_recording_path"
    ]),
    ...mapState("stimulation", ["stim_play_state"]),
    ...mapState("flask", ["status_uuid"])
  },

  created: async function() {
    this.$store.dispatch("flask/start_status_pinging");
  },
  methods: {
    send_confirmation: function(idx) {
      this.$store.commit("settings/set_confirmation_request", false);
    }
  }
};
</script>

<style type="text/css">
body {
  background-color: #000000;
}

.div__nuxt-page {
  position: absolute;
  top: 0px;
  left: 289px;
}

/* ACCORDIAN*/
#stim-studio-card {
  padding-bottom: 10px;
  width: 390px;
}

#data-acquisition-card {
  padding: 5px 0px 10px 0px;
}

.div__accordian-container {
  top: 45px;
  position: absolute;
  width: 287px;
}

.div__accordian-tabs {
  background-color: #000;
  color: #b7b7b7;
  font-family: Muli;
  width: 287px;
  height: 40px;
  border-top: 2px solid #1c1c1c;
  border-bottom: 2px solid #1c1c1c;
  border-left: 1px solid #000;
  border-right: 1px solid #000;
  text-align: left;
  padding-top: 5px;
  padding-left: 15px;
}

.div__accordian-tabs:hover,
.div__accordian-tabs-visible:hover {
  background-color: #b7b7b7c9;
  color: #000;
}

.div__accordian-tabs-visible {
  background-color: #b7b7b7;
  color: #000;
}

/* NON-SPECIFIC */
.div__arrow {
  position: relative;
  top: -13px;
  left: 245px;
  border-left: 4px solid transparent;
  border-right: 4px solid transparent;
  border-top: 6px solid #b7b7b7c9;
  width: 9px;
  transform: rotateZ(0deg) translateY(0px);
  transition-duration: 0.3s;
  transition-timing-function: cubic-bezier(0.59, 1.39, 0.37, 1.01);
}

.expanded {
  transform: rotateZ(180deg) translateY(2px);
  border-top: 6px solid #000;
}

.arrow_hover {
  border-top: 6px solid #000;
}

.div__top-bar-above-waveforms {
  position: absolute;
  left: 289px;
  background-color: #111111;
  height: 45px;
  width: 1629px;
}

.div__recording-top-bar-container {
  float: right;
  position: relative;
  height: 45px;
  width: 650px;
  display: flex;
  justify-content: space-between;
  text-align: left;
}

.div__sidebar {
  background-color: #1c1c1c;
  position: absolute;
  top: 0px;
  left: 0px;
  height: 930px;
  width: 287px;
}

.div__sidebar-page-divider {
  position: absolute;
  top: 0px;
  left: 287px;
  width: 2px;
  height: 930px;
  background-color: #0e0e0e;
}

/* DATA-ACQUISITION */
.div__screen-view-container {
  position: relative;
  width: 287px;
  display: grid;
  grid-template-columns: 50% 50%;
  justify-items: center;
}

.div__plate-barcode-container {
  position: relative;
  left: 0px;
}

.div__status-bar-container {
  position: relative;
  left: 0px;
}

.div__plate-navigator-container {
  position: relative;
  top: 5px;
  left: 0px;
}

.div__screen-view-options-text {
  line-height: 100%;
  position: relative;
  width: 207px;
  height: 23px;
  left: 11px;
  padding: 5px;
  user-select: none;
  font-size: 16px;
  color: #ffffff;
  text-align: left;
  margin: 10px;
}

.div__waveform-screen-view- {
  grid-column: 1 / 2;
}

.div__heatmap-screen-view- {
  grid-column: 2;
}

.div__player-controls-container {
  position: relative;
  left: 0px;
  margin: 5px 0;
}

/* STIM STUDIO */
.div__stim-status-container {
  position: relative;
  margin-top: 8px;
}

.div__stim-barcode-container {
  position: relative;
  left: 0px;
  margin-top: 10px;
}

.div__stimulation_controls-controls-icon-container {
  position: relative;
  margin-top: 3px;
  left: 0px;
  overflow: hidden;
}

.div__stim-studio-screen-view {
  position: absolute;
  top: 32px;
  left: 7px;
  width: 44px;
  height: 44px;
  opacity: 0;
}

/* STIMULATION/COPYRIGHT */
.div__simulation-mode-container {
  position: absolute;
  top: 875px;
}

.span__copyright {
  position: absolute;
  z-index: 99;
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
  box-sizing: border-box;
  line-height: 100%;
  overflow: hidden;
  width: 286px;
  height: 16px;
  top: 907px;
  left: -0.252101px;
  padding: 5px;
  user-select: none;
  font-family: Muli;
  font-weight: normal;
  font-style: normal;
  text-decoration: none;
  font-size: 9px;
  color: #ffffff;
  text-align: center;
}
</style>
