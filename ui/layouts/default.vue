<template>
  <div>
    <div class="div__sidebar">
      <div class="div__sidebar-page-divider" />
      <div class="div__component-container">
        <div class="div__plate-barcode-container">
          <BarcodeViewer />
        </div>
        <div class="div__stim-barcode-container">
          <BarcodeViewer :barcodeType="'stimBarcode'" />
        </div>
        <div class="div__stim-status-container">
          <StatusBar @send-confirmation="sendConfirmation" />
        </div>
        <div class="div__StimulationStudioControls-controls-icon-container">
          <StimulationStudioControls />
        </div>
        <div class="div__simulation-mode-container">
          <SimulationMode />
        </div>
        <span class="span__copyright"
          >&copy;{{ currentYear }} Curi Bio. All Rights Reserved. Version:
          {{ packageVersion }}
        </span>
      </div>
    </div>
    <div class="div__top-header-bar">
      <div v-if="stimPlayState" class="div__offline-status-banner-container">{{ offlineStatusText }}</div>
    </div>
    <div class="div__nuxt-page">
      <nuxt />
    </div>
  </div>
</template>
<script>
import Vue from "vue";

import BarcodeViewer from "@/components/status/BarcodeViewer";
import StimulationStudioControls from "@/components/stimulation/StimulationStudioControls";
import StatusBar from "@/components/status/StatusBar";
import SimulationMode from "@/components/status/SimulationMode";

import { SYSTEM_STATUS } from "@/store/modules/system/enums";
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
    StimulationStudioControls,
  },
  data: function () {
    return {
      packageVersion: "",
      currentYear: "2025", // TODO look into better ways of handling this. Not sure if just using the system's current year is the best approach
    };
  },
  computed: {
    ...mapState("stimulation", ["stimPlayState"]),
    ...mapState("system", ["statusUuid", "allowSwUpdateInstall"]),
    offlineStatusText: function () {
      return this.statusUuid === SYSTEM_STATUS.OFFLINE_STATE
        ? "Stimulation in Progress - Offline Mode"
        : "Stimulation in Progress - Online Mode";
    },
  },
  methods: {
    sendConfirmation: function (idx) {
      this.$store.commit("system/setConfirmationRequest", false);
    },
  },
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
.div__component-container {
  top: 45px;
  position: absolute;
  width: 287px;
}

/* NON-SPECIFIC */
.div__top-header-bar {
  position: absolute;
  left: 289px;
  background-color: #111111;
  height: 45px;
  width: 1629px;
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

.div__offline-status-banner-container {
  position: absolute;
  width: 400px;
  height: 45px;
  background: #f44336;
  color: white;
  text-align: center;
  left: 484px;
  font-size: 12px;
  line-height: 3.4;
}

/* DATA-ACQUISITION */
.div__plate-barcode-container {
  position: relative;
  left: 0px;
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

.div__StimulationStudioControls-controls-icon-container {
  position: relative;
  margin-top: 3px;
  left: 0px;
  overflow: hidden;
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
