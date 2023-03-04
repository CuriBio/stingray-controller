<template>
  <div class="div__plate-barcode">
    <span class="span__plate-barcode-text" :style="dynamicLabelStyle">{{ barcodeLabel }}</span>
    <input
      id="plateinfo"
      :disabled="isDisabled"
      type="text"
      spellcheck="false"
      class="input__plate-barcode-entry"
      :class="[barcodeInfo.valid ? `input__plate-barcode-entry-valid` : `input__plate-barcode-entry-invalid`]"
      :value="barcodeInfo.value"
      @input="setBarcodeManually"
    />
    <div
      v-if="barcodeManualMode && activeProcesses"
      v-b-popover.hover.top="tooltipText"
      :title="barcodeLabel"
      class="div__disabled-input-popover"
    />
    <div
      v-show="!barcodeManualMode"
      v-b-popover.hover.top="tooltipText"
      :title="barcodeLabel"
      class="input__plate-barcode-manual-entry-enable"
    >
      <span class="input__plate-barcode-manual-entry-enable-icon">
        <div id="edit-plate-barcode" @click="activeProcesses || $bvModal.show('edit-plate-barcode-modal')">
          <FontAwesomeIcon :icon="['fa', 'pencil-alt']" />
        </div>
      </span>
    </div>
    <b-modal id="edit-plate-barcode-modal" size="sm" hide-footer hide-header hide-header-close>
      <StatusWarningWidget :modalLabels="barcodeManualLabels" @handleConfirmation="handleManualModeChoice" />
    </b-modal>
    <b-modal id="barcode-warning" size="sm" hide-footer hide-header hide-header-close>
      <StatusWarningWidget :modalLabels="barcodeWarningLabels" @handleConfirmation="closeWarningModal" />
    </b-modal>
  </div>
</template>
<script>
import { mapState } from "vuex";
import { library } from "@fortawesome/fontawesome-svg-core";
import { faPencilAlt } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import StatusWarningWidget from "@/components/status/StatusWarningWidget.vue";
import Vue from "vue";
import { VBPopover } from "bootstrap-vue";
Vue.directive("b-popover", VBPopover);

library.add(faPencilAlt);
/**
 * @vue-data {String} playbackStateEnums - Current state of playback
 * @vue-computed {String} playbackState - Current value in Vuex store
 * @vue-event {String} setBarcodeManually - User entered String parser
 */
export default {
  name: "BarcodeViewer",
  components: {
    FontAwesomeIcon,
    StatusWarningWidget,
  },
  props: {
    barcodeType: { type: String, default: "plateBarcode" },
  },
  data() {
    return {
      barcodeManualLabels: {
        header: "Warning!",
        msgOne: "Do you want to enable manual barcode editing?",
        msgTwo:
          "Once enabled, all barcodes must be entered manually. This should only be done if the barcode scanner is malfunctioning. Scanning cannot be re-enabled until software is restarted.",
        buttonNames: ["Cancel", "Yes"],
      },
      barcodeWarningLabels: {
        header: "Warning!",
        msgOne: "A new barcode has been detected while a process was active.",
        msgTwo: "All processes have been stopped.",
        buttonNames: ["Okay"],
      },
    };
  },
  computed: {
    ...mapState("playback", ["barcodes", "barcodeWarning"]),
    ...mapState("flask", ["barcodeManualMode"]),
    barcodeInfo: function () {
      return this.barcodes[this.barcodeType];
    },
    barcodeLabel: function () {
      return this.barcodeType == "plateBarcode" ? "Plate Barcode:" : "Stim Lid Barcode:";
    },
    dynamicLabelStyle: function () {
      return this.barcodeType == "plateBarcode" ? "left: 17px;" : "left: 0px;";
    },

    tooltipText: function () {
      return this.activeProcesses ? "Cannot edit barcodes while stimulating..." : "Click to edit";
    },
    activeProcesses: function () {
      return false;
    },
    isDisabled: function () {
      return this.activeProcesses || !this.barcodeManualMode;
    },
  },
  watch: {
    barcodeWarning: function () {
      if (this.barcodeWarning) this.$bvModal.show("barcode-warning");
    },
  },
  methods: {
    handleManualModeChoice(choice) {
      const boolChoice = Boolean(choice);
      this.$bvModal.hide("edit-plate-barcode-modal");
      this.$store.commit("flask/setBarcodeManualMode", boolChoice);
      if (boolChoice) {
        console.log("Barcode Set Manually"); // allow-log
      }
    },
    setBarcodeManually: function (event) {
      this.$store.dispatch("playback/validateBarcode", {
        type: this.barcodeType,
        newValue: event.target.value,
      });
    },
    closeWarningModal() {
      this.$bvModal.hide("barcode-warning");
      this.$store.commit("playback/setBarcodeWarning", false);
    },
  },
};
</script>
<style>
.div__plate-barcode *,
.div__plate-barcode *:before,
.div__plate-barcode *:after {
  -webkit-box-sizing: content-box;
  -moz-box-sizing: content-box;
  box-sizing: content-box;
}

.div__plate-barcode {
  position: relative;
  top: 0px;
  left: 0px;
  width: 287px;
  height: 34px;
  background: #1c1c1c;
  -webkit-box-sizing: content-box;
  box-sizing: content-box;
}

.span__plate-barcode-text {
  pointer-events: all;
  line-height: 100%;
  overflow: hidden;
  position: absolute;
  width: 278px;
  height: 23px;
  top: 2px;
  padding: 5px;
  user-select: none;
  font-family: "Muli";
  font-weight: normal;
  font-style: normal;
  text-decoration: none;
  font-size: 16px;
  color: rgb(255, 255, 255);
  text-align: left;
}

.input__plate-barcode-entry *,
.input__plate-barcode-entry *:before,
.input__plate-barcode-entry *:after {
  -webkit-box-sizing: content-box;
  -moz-box-sizing: content-box;
  box-sizing: content-box;
}

.input__plate-barcode-entry {
  padding-left: 5px;
  padding-right: 5px;
  overflow: hidden;
  white-space: nowrap;
  text-align: left;
  line-height: 24px;
  font-style: normal;
  text-decoration: none;
  font-size: 15px;
  background-color: #000000;
  color: #b7b7b7;
  font-family: Anonymous Pro;
  font-weight: normal;
  box-shadow: none;
  border: none;
  position: absolute;
  height: 24px;
  top: 3px;
  right: 27px;
  width: 105px;
}

.div__disabled-input-popover {
  position: absolute;
  height: 24px;
  width: 100px;
  top: 3px;
  right: 27px;
}

.input__plate-barcode-entry-invalid {
  border: 1px solid red;
}

.input__plate-barcode-entry-valid {
  border: 1px solid green;
}
input:focus {
  outline: none;
}

.input__plate-barcode-manual-entry-enable {
  pointer-events: all;
  position: absolute;
  width: 34px;
  height: 34px;
  top: 0px;
  left: 263px;
}

.input__plate-barcode-manual-entry-enable-icon {
  overflow: hidden;
  white-space: nowrap;
  text-align: center;
  font-weight: normal;
  transform: translateZ(0px);
  position: absolute;
  width: 24px;
  height: 24px;
  line-height: 24px;
  top: 5px;
  left: 0px;
  font-size: 14px;
  color: #b7b7b7;
}

.fa-pencil-alt:hover {
  color: #ececed;
}

.modal-backdrop {
  background-color: rgb(0, 0, 0, 0.5);
}

/* Center the edit-plate-barcode-modal pop-up dialog within the viewport */
#edit-plate-barcode-modal {
  position: fixed;
  margin: 5% auto;
  top: 15%;
  left: 0;
  right: 0;
}
</style>
