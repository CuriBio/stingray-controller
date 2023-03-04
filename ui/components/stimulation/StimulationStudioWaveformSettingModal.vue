<template>
  <div
    id="cmpD2f15f130a7c848b6dfa50e77a7bd35ad"
    class="div__stimulationstudio-current-settings-background"
    :style="pulseType === 'Monophasic' ? 'height: 550px; margin-top: 100px;' : 'height: 840px;'"
  >
    <span id="cmpD5b2290fff52de686574ddc4481707a03" class="span__stimulationstudio-current-settings-title"
      >{{ pulseType }}&nbsp;<wbr />Pulse&nbsp;<wbr />Details
    </span>
    <div class="div__color-block" :style="colorToDisplay" />
    <div class="div__color-label" @click="$bvModal.show('change-color-modal')">Change color</div>
    <span>
      <b-modal id="change-color-modal" size="sm" hide-footer hide-header hide-header-close :static="true">
        <StimulationStudioColorModal :currentColor="selectedColor" @change-pulse-color="changePulseColor" />
      </b-modal>
    </span>
    <canvas id="cmpD1bd9abe7f57064ecc21010fe87aa8e0a" :style="'top: 59px; width: 900px'" />
    <span id="cmpD334cd34b00ad111c21b729fee2b1def2" class="span__stimulationstudio-current-settings-sub-title"
      >Phase&nbsp;<wbr />1</span
    >
    <span
      id="cmpD31286f8dd12f44eb6bfea7751c014f90"
      class="span__stimulationstudio-current-settings-label-left"
      :style="'top: 109.5px;'"
      >Stimulus&nbsp;<wbr />Duration</span
    >
    <div
      id="cmpD830cdea88a8752e1fdd278dd0215b99d"
      class="div__stimulationstudio-input-container"
      :style="'top: 96px;'"
    >
      <span id="cmpD830cdea88a8752e1fdd278dd0215b99dTxt" class="span__stimulationstudio-input">
        <InputWidget
          :placeholder="'10'"
          :domIdSuffix="'duration'"
          :invalidText="errMsgs.phaseOneDuration"
          :inputWidth="142"
          :initialValue="selectedPulseSettings.phaseOneDuration.toString()"
          @update:value="checkValidity($event, 'phaseOneDuration')"
        />
        >
      </span>
    </div>
    <span
      id="cmpDad40b728ec40e75944b1291803f7785b"
      class="span__stimulationstudio-current-settings-label-right"
      :style="'top: 109.5px;'"
      >milliseconds</span
    >
    <span
      id="cmpDf2d0dbfd2edb4ffa3b8615863fa1b9a7"
      class="span__stimulationstudio-current-settings-label-left"
      :style="'top: 179.5px;'"
      >{{ stimulationType }}</span
    >
    <div
      id="cmpDf6ba8560cb2fbd91276a29c46743e99a"
      class="div__stimulationstudio-input-container"
      :style="'top: 166px;'"
    >
      <span id="cmpDf6ba8560cb2fbd91276a29c46743e99aTxt" class="span__stimulationstudio-input">
        <InputWidget
          :placeholder="'100'"
          :domIdSuffix="'charge'"
          :invalidText="errMsgs.phaseOneCharge"
          :inputWidth="142"
          :initialValue="selectedPulseSettings.phaseOneCharge.toString()"
          @update:value="checkValidity($event, 'phaseOneCharge')"
        />
      </span>
    </div>
    <span
      id="cmpD7695902a49c6eaeb81d267812f0a90cd"
      class="span__stimulationstudio-current-settings-label-right"
      :style="'top: 179.5px;'"
      >{{ stimUnit }}</span
    >
    <div v-if="pulseType === 'Biphasic'">
      <canvas id="cmpDefb479b0caa166978ebed24ab8c44baf" :style="'top: 246px;'" />
      <span
        id="cmpD1258ad074a6b3eb7b8a869173413256d"
        class="span__stimulationstudio-current-settings-label-left"
        :style="'top: 279.5px;'"
        >Interphase&nbsp;<wbr />Interval</span
      >
      <div
        id="cmpD948f417edcd29d68f5801d54232d9431"
        class="div__stimulationstudio-input-container"
        :style="'top: 266px;'"
      >
        <span id="cmpD948f417edcd29d68f5801d54232d9431Txt" class="span__stimulationstudio-input">
          <InputWidget
            :placeholder="'10'"
            :domIdSuffix="'interphase'"
            :invalidText="errMsgs.interphaseInterval"
            :inputWidth="142"
            :initialValue="selectedPulseSettings.interphaseInterval.toString()"
            @update:value="checkValidity($event, 'interphaseInterval')"
          />
        </span>
      </div>
      <span class="span__stimulationstudio-current-settings-label-right" :style="'top: 279.5px;'"
        >milliseconds</span
      >
      <canvas id="cmpDa2bea934b07f6b108e90d5efecf200a3" :style="'top: 346px;'" />
      <span
        id="cmpD25434fb95b0bdb4dd6d951c83f90ad78"
        class="span__stimulationstudio-current-settings-sub-title"
        :style="'top: 353.5px;'"
      >
        Phase&nbsp;<wbr />2</span
      >
      <span
        id="cmpDf5881fe2782d4268a11a2a95a99d21b1"
        class="span__stimulationstudio-current-settings-label-left"
        :style="'top: 396.5px;'"
        >Stimulus&nbsp;<wbr />Duration</span
      >
      <div
        id="cmpD818347e832e1274793ffe2c57a5d0a9c"
        class="div__stimulationstudio-input-container"
        :style="'top: 383px;'"
      >
        <span id="cmpD818347e832e1274793ffe2c57a5d0a9cTxt" class="span__stimulationstudio-input">
          <InputWidget
            :placeholder="'10'"
            :domIdSuffix="'durationtwo'"
            :invalidText="errMsgs.phaseTwoDuration"
            :inputWidth="142"
            :initialValue="selectedPulseSettings.phaseTwoDuration.toString()"
            @update:value="checkValidity($event, 'phaseTwoDuration')"
          />
        </span>
      </div>
      <span
        id="cmpD470ae881458be847aa3ef17c347d3973"
        class="span__stimulationstudio-current-settings-label-right"
        :style="'top: 396.5px;'"
        >milliseconds</span
      >
      <span
        id="cmpDdd1b9fc6423c3af17206292a54489078"
        class="span__stimulationstudio-current-settings-label-left"
        :style="'top: 466.5px;'"
        >{{ stimulationType }}</span
      >
      <div
        id="cmpD8ecdf9c4a418509adff741b988ad0676"
        class="div__stimulationstudio-input-container"
        :style="'top: 453px;'"
      >
        <span id="cmpD8ecdf9c4a418509adff741b988ad0676Txt" class="span__stimulationstudio-input">
          <InputWidget
            :placeholder="'-100'"
            :domIdSuffix="'chargetwo'"
            :invalidText="errMsgs.phaseTwoCharge"
            :inputWidth="142"
            :initialValue="selectedPulseSettings.phaseTwoCharge.toString()"
            @update:value="checkValidity($event, 'phaseTwoCharge')"
          />
        </span>
      </div>
      <span
        id="cmpDbc629158eb67226e3134f41509394ec9"
        class="span__stimulationstudio-current-settings-label-right"
        :style="'top: 466.5px;'"
        >{{ stimUnit }}</span
      >
    </div>
    <canvas :style="pulseType === 'Monophasic' ? 'top: 240px;' : 'top: 533px;'" />
    <span
      class="span__stimulationstudio-current-settings-label-left"
      :style="pulseType === 'Monophasic' ? 'top: 267.5px;' : 'top: 553.5px;'"
      >Pulse Frequency</span
    >
    <div
      class="div__stimulationstudio-input-container"
      :style="pulseType === 'Monophasic' ? 'top: 253px;' : 'top: 540px;'"
    >
      <span class="span__stimulationstudio-input">
        <InputWidget
          :placeholder="'5'"
          :domIdSuffix="'pulse-frequency'"
          :invalidText="errMsgs.pulseFrequency"
          :inputWidth="142"
          :initialValue="inputPulseFrequency.toString()"
          @update:value="updateFreq($event)"
        />
      </span>
    </div>
    <span
      class="span__stimulationstudio-current-settings-label-right"
      :style="pulseType === 'Monophasic' ? 'top: 267.5px;' : 'top: 553.5px;'"
      >Hz</span
    >
    <span
      class="span__stimulationstudio-current-settings-label-left"
      :style="pulseType === 'Monophasic' ? 'top: 337.5px;' : 'top: 623.5px;'"
      >Active Duration</span
    >
    <div
      class="div__stimulationstudio-input-container"
      :style="pulseType === 'Monophasic' ? 'top: 323px;' : 'top: 610px;'"
    >
      <span class="span__stimulationstudio-input">
        <InputWidget
          :placeholder="useNumCycles ? '-' : '1000'"
          :domIdSuffix="'total-active-duration'"
          :disabled="useNumCycles"
          :invalidText="errMsgs.totalActiveDuration"
          :inputWidth="142"
          :initialValue="calculatedActiveDur.toString()"
          @update:value="updateActiveDuration($event)"
        />
      </span>
    </div>
    <span
      class="span__stimulationstudio-current-settings-label-right"
      :style="pulseType === 'Monophasic' ? 'top: 337.5px;' : 'top:  623.5px'"
    >
      <SmallDropDown
        :inputHeight="25"
        :inputWidth="100"
        :optionsText="timeUnits"
        :optionsIdx="activeDurationIdx"
        :domIdSuffix="'timeUnits'"
        @selection-changed="handleTotalDurationUnitChange"
      />
    </span>
    <div
      class="div__stimulationstudio-checkbox-container"
      :style="pulseType === 'Monophasic' ? 'top: 400px;' : 'top:  684px'"
    >
      <CheckBoxWidget
        :checkboxOptions="checkboxOptions"
        :reset="checkboxReset"
        :initialSelected="checkboxState"
        @checkbox-selected="setUseNumCycles"
      />
      <span>Use Num Cycles instead of Active Duration</span>
    </div>
    <span
      class="span__stimulationstudio-current-settings-label-left"
      :style="pulseType === 'Monophasic' ? 'top: 446px;' : 'top: 730px;'"
      >Num Cycles</span
    >
    <div
      class="div__stimulationstudio-input-container"
      :style="pulseType === 'Monophasic' ? 'top: 430px;' : 'top: 714px;'"
    >
      <span class="span__stimulationstudio-input">
        <InputWidget
          :placeholder="useNumCycles ? '100' : '-'"
          :domIdSuffix="'num-cycles'"
          :disabled="!useNumCycles"
          :invalidText="errMsgs.numCycles"
          :inputWidth="142"
          :initialValue="calculatedNumCycles.toString()"
          @update:value="updateNumCycles($event)"
        />
      </span>
    </div>
    <canvas
      :class="
        pulseType === 'Monophasic'
          ? 'canvas__monophasic-vertical-divider'
          : 'canvas__biphasic-vertical-divider'
      "
    />
    <div class="div__waveform-preview-title">Waveform Preview</div>
    <div class="div__pulse-diagram-container">
      <img
        :src="require(`@/assets/img/${pulseType}-diagram-${stimulationType}.png`)"
        :class="pulseType === 'Monophasic' ? 'img__mononphasic-diagram' : 'None'"
      />
    </div>
    <div
      class="div__waveform-diagram-descriptors"
      :class="pulseType === 'Monophasic' ? 'div__mononphasic-diagram-descriptors' : 'None'"
    >
      <span :style="'font-size: 19px; padding-bottom:15px;'">Waveform Key</span>
      <ol id="ul__waveformListItems" :style="'list-style-type: none; padding: 0px;'">
        <li v-for="key in diagramKeys[pulseType]" :key="key">{{ key }}</li>
      </ol>
    </div>
    <div class="button-container" :style="pulseType === 'Monophasic' ? 'top: 543px;' : 'top: 790px;'">
      <ButtonWidget
        :id="'button-widget-id'"
        :buttonWidgetWidth="950"
        :buttonWidgetHeight="50"
        :buttonWidgetTop="0"
        :buttonWidgetLeft="0"
        :buttonNames="buttonLabels"
        :hoverColor="buttonHoverColors"
        :isEnabled="isEnabledArray"
        @btn-click="close"
      />
    </div>
  </div>
</template>
<script>
import Vue from "vue";
import SmallDropDown from "@/components/basic-widgets/SmallDropDown.vue";
import InputWidget from "@/components/basic-widgets/InputWidget.vue";
import CheckBoxWidget from "@/components/basic-widgets/CheckBoxWidget.vue";
import StimulationStudioColorModal from "@/components/stimulation/StimulationStudioColorModal.vue";
import ButtonWidget from "@/components/basic-widgets/ButtonWidget.vue";
import { library } from "@fortawesome/fontawesome-svg-core";
import { faBalanceScale, faQuestionCircle } from "@fortawesome/free-solid-svg-icons";
import { VBPopover } from "bootstrap-vue";
import { MIN_SUBPROTOCOL_DURATION_MS, TIME_CONVERSION_TO_MILLIS } from "@/store/modules/stimulation/enums";
import { MAX_SUBPROTOCOL_DURATION_MS } from "../../store/modules/stimulation/enums";
import BootstrapVue from "bootstrap-vue";
import { BModal } from "bootstrap-vue";
Vue.directive("b-popover", VBPopover);
Vue.component("BModal", BModal);
Vue.use(BootstrapVue);
Vue.directive("popover", VBPopover);
library.add(faBalanceScale, faQuestionCircle);

/**
 * @vue-props {String} stimulationType - Current type of stimulation
 * @vue-props {String} pulseType - Type of pulse for modal
 * @vue-props {Object} selectedPulseSettings - Settings passed to modal if it's selected to edit
 * @vue-props {Object} selectedPulseSettings - Stim block settings passed to modal if it's selected to edit
 * @vue-props {Object} openModalForEdit - Boolean to determine if modal is open with existing settings
 * @vue-data {String} popoverMessage - Popover for disabled input field on hover of question mark
 * @vue-data {Object} pulseSettings - Model for new inputs to be assigned
 * @vue-data {Object} pulseSettings - Model for new inputs to be assigned
 * @vue-data {Array} isEnabledArray - Array of which buttons should be disabled at base of modal
 * @vue-data {Object} invalidErrMsg - Object containing all error messages for validation checks of inputs
 * @vue-data {Object} errMsgs - Object containing all initial error messages for inputs
 * @vue-data {Boolean} allValid - True if all inputs pass the validation check and allows Save button to become enabled
 * @vue-data {Object} timeUnits - Contains option for dropdown components
 * @vue-data {Integer} delayIntervalIdx - Used to input current delay interval setting to dropdown when open for edit
 * @vue-data {Integer} activeDurationIdx - Used to input current active duration setting to dropdown when open for edit
 * @vue-computed {String} checkMaxType - Computes last label for disabled input field
 * @vue-computed {Array} buttonLabels - Array of button labels for modal
 * @vue-computed {Array} hoveredButtonColors - Array of colors that the text will be when a button is hovered over
 * @vue-method {event} close - emits close of modal and data to parent component
 * @vue-method {event} checkValidity - calls appropriate validation checks based on changes to inputs
 * @vue-method {event} handleAllValid - checks if all inputs are valid numbers only and not empty
 * @vue-method {event} checkPulseDuration - checks if the pulse durations are all positive integers and less than 50ms
 * @vue-method {event} checkActiveDuration - checks if total duration is greater than entire pulse duration and a positive integer
 * @vue-method {event} checkDelayInterval - checks if delay interval is a positive integer
 * @vue-method {event} checkChargeValidity - checks if charge is greater than or less than set range for voltage(1200) and current(100)
 * @vue-method {event} handleTotalDurationUnitChange - handles change to unit dropdown for total active duration input
 * @vue-method {event} handleDelayUnitChange - handles change to unit dropdown for delay interval input
 */

export default {
  name: "StimulationStudioWaveformSettingModal",
  components: {
    InputWidget,
    ButtonWidget,
    SmallDropDown,
    CheckBoxWidget,
    StimulationStudioColorModal,
  },
  props: {
    stimulationType: { type: String, default: "Current" },
    pulseType: { type: String, default: "Biphasic" },
    modalOpenForEdit: { type: Boolean, default: false },
    selectedPulseSettings: {
      type: Object,
      required: true,
    },
    currentColor: {
      type: String,
      default: null,
    },
  },
  data() {
    return {
      popoverMessage: "Not Editable: This data is displayed for informational purposes only.",
      pulseSettings: {},
      invalidErrMsg: {
        numErr: "Must be a number",
        minNumErr: "Must be a positive number",
        required: "Required",
        maxPulseDuration: "Duration must be <= 50ms",
        minActiveDuration: "Duration must be >= 100ms",
        valid: "",
        maxCurrent: "Must be within +/- 100",
        maxVoltage: "Must be within +/- 1200",
        frequency: "Must be a non-zero value <= 100",
        numCycles: "Must be a whole number > 0",
      },
      errMsgs: {
        phaseOneDuration: "",
        phaseOneCharge: "",
        interphaseInterval: "",
        phaseTwoDuration: "",
        phaseTwoCharge: "",
        pulseFrequency: "",
        totalActiveDuration: "",
        numCycles: "",
      },
      timeUnits: ["milliseconds", "seconds", "minutes", "hours"],
      allValid: false,
      isEnabledArray: [false, true],
      activeDurationIdx: 0,
      inputPulseFrequency: "",
      maxPulseDurationForFreq: 50,
      diagramKeys: {
        Monophasic: ["A. Phase Duration", `B. Phase ${this.stimulationType}`, "C. Total Active Duration"],
        Biphasic: [
          "A. Phase 1 Duration",
          `B. Phase 1 ${this.stimulationType}`,
          "C. Interphase Interval",
          "D. Phase 2 Duration",
          `E. Phase 2 ${this.stimulationType}`,
          "F. Total Active Duration",
        ],
      },
      calculatedActiveDur: "",
      calculatedNumCycles: "",
      numCycles: "",
      useNumCycles: false,
      checkboxOptions: [{ text: "", value: "useNumCycles" }],
      checkboxReset: false,
      checkboxState: false,
      selectedColor: this.currentColor,
    };
  },
  computed: {
    totalPulseDuration: function () {
      return this.pulseType === "Monophasic"
        ? +this.pulseSettings.phaseOneDuration
        : +this.pulseSettings.phaseOneDuration +
            +this.pulseSettings.phaseTwoDuration +
            +this.pulseSettings.interphaseInterval;
    },
    calculatedDelay: function () {
      const totalDelay = 1000 - this.inputPulseFrequency * this.totalPulseDuration;
      return totalDelay / this.inputPulseFrequency;
    },
    stimUnit: function () {
      return this.stimulationType.includes("C") ? "mA" : "V";
    },
    buttonHoverColors: function () {
      return this.modalOpenForEdit ? ["#19ac8a", "#19ac8a", "#bd4932", "#bd4932"] : ["#19ac8a", "#bd4932"];
    },
    buttonLabels: function () {
      return this.modalOpenForEdit ? ["Save", "Duplicate", "Delete", "Cancel"] : ["Save", "Cancel"];
    },
    colorToDisplay: function () {
      return "background-color: " + this.selectedColor;
    },
  },
  watch: {
    allValid() {
      this.setIsEnabledArray();
    },
  },
  created() {
    // Need to copy these values so that the original values won't be edited in case the user cancels an edit
    this.pulseSettings = JSON.parse(JSON.stringify(this.selectedPulseSettings));

    if (this.pulseSettings.frequency !== 0) this.inputPulseFrequency = this.pulseSettings.frequency;

    const { unit, duration } = this.pulseSettings.totalActiveDuration;
    this.activeDurationIdx = this.timeUnits.indexOf(unit);

    // Tanner (9/27/22): Currently this modal will always load with useNumCycles set to false, so need to set these specific values
    this.calculatedActiveDur = duration;
    this.updateCalculatedNumCycles();
    this.numCycles = this.calculatedNumCycles;

    for (const input in this.pulseSettings) {
      if (this.pulseSettings !== {}) {
        const value = this.pulseSettings[input];
        this.checkValidity(value, input);
      }
    }

    this.checkValidity(this.inputPulseFrequency, "pulseFrequency");
    this.checkValidity(duration, "totalActiveDuration");
    this.checkValidity(this.numCycles, "numCycles");
    this.setIsEnabledArray();
  },
  methods: {
    setIsEnabledArray() {
      // disabled duplicate and save button if not valid inputs
      this.isEnabledArray = this.modalOpenForEdit
        ? [this.allValid, this.allValid, true, true]
        : [this.allValid, true];
    },
    close(idx) {
      const buttonLabel = this.buttonLabels[idx];
      this.pulseSettings.postphaseInterval = this.calculatedDelay;
      this.pulseSettings.numCycles = +this.numCycles;
      this.pulseSettings.frequency = this.inputPulseFrequency;
      this.$emit("close", buttonLabel, this.pulseSettings, this.selectedColor);
    },
    updateFreq(newValue) {
      this.checkValidity(newValue, "pulseFrequency");
      this.updateCurrentCalculatedValue();
    },
    updateActiveDuration(newValue) {
      this.checkValidity(newValue, "totalActiveDuration");
      if (!this.useNumCycles) {
        this.updateCalculatedNumCycles();
      }
    },
    updateNumCycles(newValue) {
      this.checkValidity(newValue, "numCycles");
      if (this.useNumCycles) {
        this.updateCalculatedActivateDur();
      }
    },
    updateCalculatedActivateDur() {
      const defaultValue = "-";

      const isNumCyclesMissing = this.numCycles === "";
      const isFreqMissing = this.inputPulseFrequency === "";

      let updatedVal;
      if (isNumCyclesMissing && isFreqMissing) {
        // if no values have been entered, return empty string so that the placeholder value is used
        updatedVal = "";
      } else if (isNumCyclesMissing || isFreqMissing) {
        // TODO could try checking the error messages here instead
        // if only one of the values needed to calculate the active dur has been entered, return "-"
        updatedVal = defaultValue;
      } else {
        const selectedUnit = this.timeUnits[this.activeDurationIdx];

        const durationInSecs = this.numCycles / this.inputPulseFrequency;
        const durInSelectedUnits = (durationInSecs * 1000) / TIME_CONVERSION_TO_MILLIS[selectedUnit];

        updatedVal = isFinite(durInSelectedUnits) ? durInSelectedUnits : defaultValue;
      }

      this.calculatedActiveDur = updatedVal;
    },
    updateCalculatedNumCycles() {
      const defaultValue = "-";

      const isActiveDurMissing =
        !this.pulseSettings.totalActiveDuration || this.pulseSettings.totalActiveDuration.duration === "";
      const isFreqMissing = this.inputPulseFrequency === "";

      let updatedVal;
      if (isActiveDurMissing && isFreqMissing) {
        // if no values have been entered, return empty string so that the placeholder value is used
        updatedVal = this.calculatedNumCycles = "";
      } else if (isActiveDurMissing || isFreqMissing) {
        // TODO could try checking the error messages here instead
        // if only one of the values needed to calculate the number of cycles has been entered, return "-"
        updatedVal = this.calculatedNumCycles = defaultValue;
      } else {
        const selectedUnit = this.timeUnits[this.activeDurationIdx];
        const durationInSecs =
          this.pulseSettings.totalActiveDuration.duration * (TIME_CONVERSION_TO_MILLIS[selectedUnit] / 1000);

        const numCycles = durationInSecs * this.inputPulseFrequency;
        updatedVal = isFinite(numCycles) ? numCycles : defaultValue;
      }

      this.calculatedNumCycles = updatedVal;
    },
    updateCurrentCalculatedValue() {
      if (this.useNumCycles) {
        this.updateCalculatedActivateDur();
      } else {
        this.updateCalculatedNumCycles();
      }
    },
    checkValidity(value, label) {
      if (label === "numCycles") {
        this.numCycles = value;
        this.checkNumCycles();
      } else {
        if (label.includes("phase")) {
          this.pulseSettings[label] = value;
        } else if (label.includes("active")) {
          this.pulseSettings.totalActiveDuration.duration = value;
        }

        if (label.includes("duration") || label.includes("interval")) {
          this.checkPulseDurationValidity();
          this.checkActiveDuration();
        } else if (label.includes("charge")) {
          this.checkChargeValidity(value, label);
        } else if (label.includes("frequency")) {
          this.inputPulseFrequency = value;
          this.checkPulseFrequency();
        }
      }
      this.handleAllValid();
    },
    checkPulseDurationValidity() {
      this.checkPulseDuration("phaseOneDuration");
      if (this.pulseType === "Biphasic") {
        this.checkPulseDuration("phaseTwoDuration");
        this.checkPulseDuration("interphaseInterval");
      }
    },
    handleAllValid() {
      for (const msg of Object.values(this.errMsgs)) {
        if (msg !== "") {
          this.allValid = false;
          return;
        }
      }
      this.allValid = true;
    },
    checkPulseDuration(label) {
      const valueStr = this.pulseSettings[label];
      const value = +valueStr;
      if (valueStr === "") {
        this.errMsgs[label] = this.invalidErrMsg.required;
      } else if (isNaN(value) || value < 0) {
        this.errMsgs[label] = this.invalidErrMsg.minNumErr;
      } else if (this.totalPulseDuration > this.maxPulseDurationForFreq) {
        this.errMsgs[label] = this.invalidErrMsg.maxPulseDuration;
      } else {
        this.errMsgs[label] = this.invalidErrMsg.valid;
        this.pulseSettings[label] = value;
      }
    },
    checkActiveDuration() {
      const valueStr = this.pulseSettings.totalActiveDuration.duration;
      const value = +valueStr;
      const selectedUnit = this.timeUnits[this.activeDurationIdx];
      const valueInMillis = value * TIME_CONVERSION_TO_MILLIS[selectedUnit];
      // if user continues with letter in one of the duration input fields, totalPulseDuration will be NaN, so change it to 0
      const minDurAllowed = Math.max(MIN_SUBPROTOCOL_DURATION_MS, this.totalPulseDuration || 0);

      const label = "totalActiveDuration";

      if (valueStr === "") {
        this.errMsgs[label] = this.invalidErrMsg.required;
      } else if (isNaN(value)) {
        this.errMsgs[label] = "Invalid number";
      } else if (valueInMillis < minDurAllowed) {
        this.errMsgs[label] = `Must be >= ${minDurAllowed}ms`;
      } else if (valueInMillis > MAX_SUBPROTOCOL_DURATION_MS) {
        const maxInHrs = MAX_SUBPROTOCOL_DURATION_MS / TIME_CONVERSION_TO_MILLIS.hours;
        this.errMsgs[label] = `Must be <= ${maxInHrs}hrs`;
      } else {
        this.errMsgs[label] = this.invalidErrMsg.valid;
        this.pulseSettings[label].duration = value;
        this.pulseSettings[label].unit = this.timeUnits[this.activeDurationIdx];
      }
    },
    checkPulseFrequency() {
      const label = "pulseFrequency";

      const valueStr = this.inputPulseFrequency;
      const value = +valueStr;

      if (valueStr === "") {
        this.errMsgs[label] = this.invalidErrMsg.required;
      } else if (isNaN(value) || value <= 0 || value > 100) {
        this.errMsgs[label] = this.invalidErrMsg.frequency;
      } else {
        this.errMsgs[label] = this.invalidErrMsg.valid;
        this.inputPulseFrequency = value;
        this.maxPulseDurationForFreq = Math.min(50, Math.trunc((1000 / this.inputPulseFrequency) * 0.8));

        this.invalidErrMsg.maxPulseDuration = `Duration must be <= ${this.maxPulseDurationForFreq}ms`;
        this.checkPulseDurationValidity(); // Need to recheck pulse dur after a new valid frequency is entered
      }
    },
    checkChargeValidity(valueStr, label) {
      const value = +valueStr;
      if (valueStr === "") {
        this.errMsgs[label] = this.invalidErrMsg.required;
      } else if (isNaN(value)) {
        this.errMsgs[label] = this.invalidErrMsg.numErr;
      } else if (this.stimulationType.includes("C") && Math.abs(value) > 100) {
        this.errMsgs[label] = this.invalidErrMsg.maxCurrent;
      } else if (this.stimulationType.includes("V") && Math.abs(value) > 1200) {
        this.errMsgs[label] = this.invalidErrMsg.maxVoltage;
      } else {
        this.errMsgs[label] = this.invalidErrMsg.valid;
        this.pulseSettings[label] = value;
      }
    },
    checkNumCycles() {
      const numCyclesAsNum = +this.numCycles;
      let errorMsgLabel;
      if (this.numCycles === "" || !Number.isInteger(numCyclesAsNum) || numCyclesAsNum <= 0) {
        errorMsgLabel = "numCycles";
      } else {
        errorMsgLabel = "valid";
        this.numCycles = numCyclesAsNum;
      }
      this.errMsgs["numCycles"] = this.invalidErrMsg[errorMsgLabel];
    },
    handleTotalDurationUnitChange(idx) {
      this.activeDurationIdx = idx;
      this.updateCurrentCalculatedValue();
      this.checkActiveDuration();
      this.handleAllValid();
    },
    setUseNumCycles(newValue) {
      this.useNumCycles = newValue == "useNumCycles";
      this.updateCurrentCalculatedValue();
    },
    changePulseColor(color) {
      this.$bvModal.hide("change-color-modal");
      this.selectedColor = color;
    },
  },
};
</script>
<style scoped>
.div__stimulationstudio-current-settings-background {
  transform: rotate(0deg);
  box-sizing: border-box;
  padding: 0px;
  margin: 0px;
  background: rgb(17, 17, 17);
  position: absolute;
  width: 950px;
  visibility: visible;
  border: 2px solid rgb(0, 0, 0);
  border-radius: 0px;
  box-shadow: none;
  z-index: 5;
  pointer-events: all;
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
  left: calc(863px - 852px);
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

canvas {
  transform: rotate(0deg);
  pointer-events: all;
  position: absolute;
  width: 472px;
  height: 2px;
  left: calc(878px - 854px);
  visibility: visible;
  background-color: #292929;
  opacity: 0.5;
}

.span__stimulationstudio-current-settings-sub-title {
  pointer-events: all;
  line-height: 100%;
  transform: rotate(0deg);
  overflow: hidden;
  position: absolute;
  width: 499px;
  height: 30px;
  top: calc(122.5px - 55px);
  left: calc(863px - 852px);
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

.button-container {
  left: -1px;
  position: absolute;
  cursor: pointer;
}

.span__stimulationstudio-current-settings-label-left {
  pointer-events: all;
  line-height: 100%;
  transform: rotate(0deg);
  overflow: visible;
  position: absolute;
  width: 156px;
  height: 30px;
  left: calc(873px - 852px);
  padding: 5px;
  visibility: visible;
  user-select: none;
  font-family: Muli;
  font-weight: normal;
  font-style: normal;
  text-decoration: none;
  font-size: 17px;
  color: rgb(183, 183, 183);
  text-align: right;
}

.span__stimulationstudio-current-settings-label-right {
  pointer-events: all;
  line-height: 100%;
  transform: rotate(0deg);
  position: absolute;
  width: 128px;
  height: 25px;
  left: calc(1195.28px - 852px);
  padding: 5px;
  visibility: visible;
  user-select: none;
  font-family: Muli;
  font-weight: normal;
  font-style: normal;
  text-decoration: none;
  font-size: 15px;
  color: rgb(183, 183, 183);
  text-align: left;
  z-index: 4;
}

.div__stimulationstudio-checkbox-container {
  pointer-events: all;
  line-height: 100%;
  transform: rotate(0deg);
  overflow: visible;
  position: absolute;
  width: 365px;
  height: 30px;
  left: calc(900px - 852px);
  padding: 5px;
  visibility: visible;
  user-select: none;
  font-family: Muli;
  font-weight: normal;
  font-style: normal;
  text-decoration: none;
  font-size: 17px;
  color: rgb(183, 183, 183);
  text-align: right;
}

.div__color-block {
  height: 14px;
  width: 14px;
  top: 24px;
  left: 450px;
  position: absolute;
  border: 1px solid rgb(255, 255, 255);
}

.div__color-label {
  font-style: italic;
  color: rgb(255, 255, 255);
  position: absolute;
  font-size: 13px;
  left: 475px;
  top: 22px;
  cursor: pointer;
}
.span__stimulationstudio-input {
  white-space: nowrap;
  text-align: left;
  font-weight: normal;
  transform: translateZ(0px);
  position: absolute;
  width: 150px;
  height: 90px;
  line-height: 45px;
  top: 6px;
  left: 6px;
  user-select: none;
  font-family: Anonymous Pro;
  font-style: normal;
  text-decoration: none;
  font-size: 17px;
  color: rgb(255, 255, 255);
}

.div__stimulationstudio-input-container {
  pointer-events: all;
  transform: rotate(0deg);
  overflow: hidden;
  position: absolute;
  width: 200px;
  height: 90px;
  left: calc(1031px - 852px);
  visibility: visible;
}

.canvas__biphasic-vertical-divider {
  transform: rotate(90deg);
  left: 170px;
  top: 425px;
  width: 695px;
}

.canvas__monophasic-vertical-divider {
  transform: rotate(90deg);
  left: 300px;
  top: 300px;
  width: 440px;
}

.div__pulse-diagram-container {
  position: absolute;
  left: 540px;
  top: 110px;
}

.div__waveform-preview-title {
  position: absolute;
  user-select: none;
  font-family: Muli;
  font-weight: normal;
  font-style: normal;
  font-size: 19px;
  color: rgb(255, 255, 255);
  text-align: center;
  left: 650px;
  top: calc(122.5px - 50px);
}

.div__waveform-diagram-descriptors {
  position: absolute;
  height: 150px;
  left: 560px;
  top: 470px;
  width: 370px;
  font-size: 15px;
  color: rgb(183, 183, 183);
  text-align: left;
}

.img__mononphasic-diagram {
  width: 350px;
  margin-left: 50px;
  max-width: 260px;
  max-height: 300px;
}

.div__mononphasic-diagram-descriptors {
  top: 430px;
  font-size: 14px;
}

#change-color-modal {
  position: fixed;
  top: 5%;
  left: 30%;
  height: 300px;
}
</style>
