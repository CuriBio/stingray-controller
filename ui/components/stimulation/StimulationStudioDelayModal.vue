<template>
  <div class="div__stimulationstudio-current-settings-background">
    <span class="span__stimulationstudio-current-settings-title"
      >{{ modalTitle }}
      <div class="div__color-block" :style="colorToDisplay" />
      <div class="div__color-label" @click="$bvModal.show('change-color-modal-two')">Change color</div></span
    >
    <span>
      <b-modal id="change-color-modal-two" size="sm" hide-footer hide-header hide-header-close :static="true">
        <StimulationStudioColorModal :currentColor="selectedColor" @change-pulse-color="changePulseColor" />
      </b-modal>
    </span>
    <canvas class="canvas__stimulationstudio-horizontal-line-separator"> </canvas>
    <div class="div__stimulationstudio-body-container">
      <span>{{ inputDescription }}</span>
      <span class="input_container">
        <InputWidget
          :placeholder="'0'"
          :domIdSuffix="'delay'"
          :invalidText="invalidText"
          :inputWidth="100"
          :initialValue="currentValue !== null ? currentValue : ''"
          @update:value="checkValidity($event)"
        />
      </span>
      <span>
        <SmallDropDown
          :optionsText="timeUnits"
          :optionsIdx="timeUnitIdx"
          :inputHeight="25"
          :inputWidth="100"
          :domIdSuffix="'delayBlock'"
          @selection-changed="handleUnitChange"
        />
      </span>
    </div>
    <div :class="'button-container'">
      <ButtonWidget
        :id="'button-widget-id'"
        :buttonWidgetWidth="520"
        :buttonWidgetHeight="50"
        :buttonWidgetTop="0"
        :buttonWidgetLeft="-1"
        :buttonNames="buttonLabels"
        :hoverColor="buttonHoverColors"
        :isEnabled="isEnabledArray"
        @btn-click="close"
      />
    </div>
  </div>
</template>
<script>
import InputWidget from "@/components/basic-widgets/InputWidget.vue";
import ButtonWidget from "@/components/basic-widgets/ButtonWidget.vue";
import SmallDropDown from "@/components/basic-widgets/SmallDropDown.vue";
import StimulationStudioColorModal from "@/components/stimulation/StimulationStudioColorModal.vue";
import {
  MAX_SUBPROTOCOL_DURATION_MS,
  MIN_SUBPROTOCOL_DURATION_MS,
  TIME_CONVERSION_TO_MILLIS,
} from "@/store/modules/stimulation/enums";
import Vue from "vue";
import BootstrapVue from "bootstrap-vue";

import { BModal } from "bootstrap-vue";
import { VBPopover } from "bootstrap-vue";
Vue.directive("b-popover", VBPopover);
Vue.component("BModal", BModal);
Vue.use(BootstrapVue);
/**
 * @vue-props {String} currentValue - Current input if modal is open for editing
 * @vue-props {String} currentDelayUnit - The current unit selected when a delay block is opened to edit
 * @vue-props {String} modalType - Determines if delay or repeat styling is assigned to modal
 * @vue-props {Boolean} modalOpenForEdit - States if delay modal is open for editing
 * @vue-data {String} inputValue - Value input into modal
 * @vue-data {String} invalidText - Validity check for input
 * @vue-computed {Array} buttonLabels - Button labels for modal
 * @vue-data {Array} isEnabledArray - Array of which buttons should be disabled at base of modal
 * @vue-computed {Array} buttonHoverColors - Array of what color the text in the button will be when hovered over
 * @vue-data {Array} timeUnits - Array of possible options in the unit dropdown menu
 * @vue-data {Int} timeUnitIdx - Index of currently selected time unit from dropdown
 * @vue-data {Object} invalidErrMsg - Object containing all error messages for validation checks of inputs
 * @vue-watch {Boolean} isValid - True if input passes the validation check and allows Save button to become enabled
 * @vue-data {String} modalTitle - Title
 * @vue-data {String} inputDescription - Subtitle
 * @vue-computed {Array} buttonLabels - Button array dependent on if its a reedit or not
 * @vue-method {event} close - emits close of modal and data to parent component
 * @vue-method {event} checkValidity - checks if inputs are valid numbers only and not empty
 * @vue-method {event} handleUnitChange - Saves current selected index in time unit dropdown
 */

export default {
  name: "StimulationStudioDelayModal",
  components: {
    InputWidget,
    ButtonWidget,
    SmallDropDown,
    StimulationStudioColorModal,
  },
  props: {
    currentDelayInput: {
      type: String,
      default: null,
    },
    currentDelayUnit: {
      type: String,
      default: "milliseconds",
    },
    modalOpenForEdit: {
      type: Boolean,
      default: false,
    },
    currentColor: {
      type: String,
      default: null,
    },
  },
  data() {
    return {
      currentValue: this.currentDelayInput,
      inputValue: null,
      invalidText: "Required",
      invalidErrMsg: {
        numErr: "Must be a (+) number",
        required: "Required",
        valid: "",
        minDuration: `Duration must be >=${MIN_SUBPROTOCOL_DURATION_MS}ms`,
        maxDuration: "Duration must be <= 24hrs",
        nonInteger: "Must be a whole number of ms",
      },
      timeUnits: ["milliseconds", "seconds", "minutes", "hours"],
      timeUnitIdx: 0,
      isEnabledArray: [false, true],
      isValid: false,
      modalTitle: "Delay",
      inputDescription: "Duration:",
      selectedColor: this.currentColor,
    };
  },
  computed: {
    buttonLabels() {
      return this.modalOpenForEdit ? ["Save", "Duplicate", "Delete", "Cancel"] : ["Save", "Cancel"];
    },
    buttonHoverColors: function () {
      return this.modalOpenForEdit ? ["#19ac8a", "#19ac8a", "#bd4932", "#bd4932"] : ["#19ac8a", "#bd4932"];
    },
    colorToDisplay: function () {
      return "background-color: " + this.selectedColor;
    },
  },
  watch: {
    isValid() {
      // disabled duplicate and save button if not valid inputs
      this.isEnabledArray = this.modalOpenForEdit
        ? [this.isValid, this.isValid, true, true]
        : [this.isValid, true];
    },
  },
  created() {
    this.inputValue = this.currentValue;

    this.timeUnitIdx = this.timeUnits.indexOf(this.currentDelayUnit);
    this.isEnabledArray = this.modalOpenForEdit ? [true, true, true, true] : [false, true];
    if (this.currentValue !== null) this.checkValidity(this.inputValue);
  },
  methods: {
    close(idx) {
      const buttonLabel = this.buttonLabels[idx];

      const selectedUnit = this.timeUnits[this.timeUnitIdx];
      const convertedInput = Number(this.inputValue);
      const delaySettings = {
        duration: convertedInput,
        unit: selectedUnit,
      };

      this.$emit("delayClose", buttonLabel, delaySettings, this.selectedColor);
    },
    checkValidity(valueStr) {
      this.currentValue = valueStr;

      const value = +valueStr;

      const selectedUnit = this.timeUnits[this.timeUnitIdx];
      const valueInMillis = value * TIME_CONVERSION_TO_MILLIS[selectedUnit];

      if (valueStr === "") {
        this.invalidText = this.invalidErrMsg.required;
      } else if (isNaN(value)) {
        this.invalidText = this.invalidErrMsg.numErr;
      } else if (valueInMillis < MIN_SUBPROTOCOL_DURATION_MS) {
        this.invalidText = this.invalidErrMsg.minDuration;
      } else if (valueInMillis > MAX_SUBPROTOCOL_DURATION_MS) {
        this.invalidText = this.invalidErrMsg.maxDuration;
      } else if (!Number.isInteger(valueInMillis)) {
        this.invalidText = this.invalidErrMsg.nonInteger;
      } else {
        this.invalidText = this.invalidErrMsg.valid;
        // Only want to update inputValue here so it is only ever set to a valid value.
        // This means that if a user enters an invalid value and then presses cancel, the most recent
        // valid value will be committed to the store instead of the invalid value
        this.inputValue = value;
      }

      this.isValid = this.invalidText === this.invalidErrMsg.valid;
    },
    handleUnitChange(idx) {
      this.timeUnitIdx = idx;
      this.checkValidity(this.currentValue);
    },
    changePulseColor(color) {
      this.$bvModal.hide("change-color-modal-two");
      this.selectedColor = color;
    },
  },
};
</script>
<style>
.div__stimulationstudio-current-settings-background {
  transform: rotate(0deg);
  box-sizing: border-box;
  padding: 0px;
  margin: 0px;
  background: rgb(17, 17, 17);
  position: absolute;
  width: 522px;
  height: 250px;
  top: calc(55px - 55px);
  left: calc(852px - 852px);
  visibility: visible;
  border: 2px solid rgb(0, 0, 0);
  border-radius: 0px;
  box-shadow: none;
  z-index: 5;
  pointer-events: all;
  display: flex;
  justify-content: center;
}

.span__stimulationstudio-current-settings-title {
  pointer-events: all;
  line-height: 100%;
  transform: rotate(0deg);
  overflow: hidden;
  position: absolute;
  width: 500px;
  height: 30px;
  top: calc(72px - 55px);
  left: calc(863px - 872px);
  padding: 5px;
  visibility: visible;
  user-select: none;
  font-family: Muli;
  font-weight: normal;
  font-style: normal;
  text-decoration: none;
  font-size: 19px;
  color: rgb(255, 255, 255);
  text-align: center;
}

.canvas__stimulationstudio-horizontal-line-separator {
  transform: rotate(0deg);
  pointer-events: all;
  position: absolute;
  width: 472px;
  height: 2px;
  top: calc(104px - 45px);
  left: calc(878px - 852px);
  visibility: visible;
  background-color: #292929;
  opacity: 0.5;
}

.button-container {
  top: 210px;
  left: 0;
  position: absolute;
  cursor: pointer;
}

.input_container {
  position: relative;
  bottom: 25px;
  right: 120px;
  margin-left: 140px;
}

.div__color-block {
  height: 14px;
  width: 14px;
  top: 7px;
  left: 370px;
  position: absolute;
  border: 1px solid rgb(255, 255, 255);
}

.div__color-label {
  font-style: italic;
  color: rgb(255, 255, 255);
  position: absolute;
  font-size: 13px;
  left: 395px;
  top: 5px;
  cursor: pointer;
}

.div__color-label:hover {
  text-decoration: underline;
  cursor: pointer;
}

.div__stimulationstudio-body-container {
  display: flex;
  justify-content: center;
  align-items: center;
  line-height: 100%;
  transform: rotate(0deg);
  position: relative;
  width: 100%;
  height: 90px;
  top: 95px;
  visibility: visible;
  font-family: Muli;
  font-size: 17px;
  color: rgb(183, 183, 183);
  z-index: 5;
}

#change-color-modal-two___BV_modal_backdrop_ {
  background-color: rgb(0, 0, 0, 0);
}

#change-color-modal___BV_modal_backdrop_ {
  background-color: rgb(0, 0, 0, 0);
}

.modal-content {
  background-color: rgb(0, 0, 0, 0);
}

#change-color-modal-two {
  position: fixed;
  top: 10%;
  left: 65%;
  height: 300px;
}
</style>
