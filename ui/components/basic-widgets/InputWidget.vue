<template>
  <div>
    <div
      class="div__input-background"
      :style="`width: ${inputWidthBackground}px; height: ${inputHeightBackground}px;`"
    >
      <span v-if="titleLabel !== ''" class="span__input-content-label" :style="`width: ${inputWidth}px;`">
        {{ titleLabel }}
      </span>

      <div
        class="div__input-controls-content-widget"
        :class="[
          !inputIsValid
            ? 'div__input-controls-content-widget--invalid'
            : 'div__input-controls-content-widget--valid',
        ]"
        :style="`width: ${inputWidth}px; height: ${inputHeight}px; top: ${inputWidgetTop}px;`"
      >
        <span
          class="span__input-controls-content-input-txt-widget"
          :style="`width: ${inputWidth}px; height: ${inputHeight}px; line-height: ${inputHeight}px;`"
        >
          <b-form-input
            :id="'input-widget-field-' + domIdSuffix"
            v-model="inputValue"
            :spellcheck="spellcheck"
            :state="inputIsValid"
            aria-describedby="input-feedback"
            :placeholder="placeholder"
            :disabled="disabled"
            :onpaste="disablePaste"
            :type="type"
            class="w-100 h-100 edit-id"
            style="border-radius: 0; color: rgb(255, 255, 255); background-color: #3f3f3f; border: 0px"
            @input="onBFormInput"
          />
        </span>
      </div>
      <div
        v-show="displayTextMessage"
        :id="`input-widget-feedback-${domIdSuffix}`"
        class="div__input-controls-content-feedback"
        :style="`width: ${inputWidth}px; top: ${inputFeedbackTop}px;`"
      >
        {{ invalidText }}
      </div>
    </div>
  </div>
</template>
<script>
import Vue from "vue";
import BootstrapVue from "bootstrap-vue";
import { BFormInput } from "bootstrap-vue";
Vue.use(BootstrapVue);
Vue.component("BFormInput", BFormInput);
import "bootstrap/dist/css/bootstrap.min.css";
/* IMPORTANT NOTE ON UTILIZATION */
/* ==========================================================================================================================================*/
/* The Parent component which utilises the widget has to follow the rule when using on the dialogs or components.
   From the Mockflow page they need to extract the proper width on which the PopInput Widget has to appear and reduce the width by 4 pixels
   As the PopInput background introduces a border of 2px and surronding the <input> box the red and green validation boxes introduces 2px.
   Request you to consider for the prop assignment the following formula:-
   inputWidth = MockflowUIWidth - 4
   ==========================================================================================================================================*/
export default {
  name: "InputWidget",
  props: {
    titleLabel: { type: String, default: "" }, // titleText (str) (optional, defaults to empty string "")
    placeholder: { type: String, default: "" }, // placeholder (str)
    invalidText: { type: String, default: "" }, // invalidText (str)
    spellcheck: { type: Boolean, default: true }, // spellcheck (optional bool=True)
    initialValue: { type: String, default: "" }, // fieldValue (str) (optional, defaults to empty string "")
    topAdjust: { type: Number, default: 0 },
    inputWidth: { type: Number, default: 0 }, // textboxWidth (int)  [pixels]
    inputHeight: { type: Number, default: 45 }, // textboxWidth (int)  [pixels]
    disabled: { type: Boolean, default: false }, // disabled (optional bool=False) (not able to type into input)
    domIdSuffix: { type: String, default: "" }, // TODO (Eli 11/3/20): consider defaulting this to a random UUID if no value supplied
    displayTextMessage: { type: Boolean, default: true }, // displayTextMessage (boolean) if set to false would not render invalidText
    disablePaste: { type: Boolean, default: false }, // disablePaste (boolean) if set to true would prevent cut and paste of text into input
    type: { type: String, default: "text" },
  },
  data() {
    return {
      inputValue: this.initialValue,
      inputWidthBackground: this.inputWidth + 4, // required for the red/green boxes around the input widget
    };
  },
  computed: {
    inputIsValid: function () {
      return this.invalidText === "";
    },
    inputHeightBackground: function () {
      return this.titleLabel !== "" ? 100 : this.inputHeight + 10;
    },
    inputWidgetTop: function () {
      const base = this.titleLabel !== "" ? 40 : 0;
      return base + this.topAdjust;
    },
    inputFeedbackTop: function () {
      return this.inputHeight + this.topAdjust + 4 + (this.titleLabel !== "" ? 40 : 0);
    },
  },
  watch: {
    initialValue() {
      const specialIdSuffix =
        this.domIdSuffix.includes("heatmap") || this.domIdSuffix.includes("protocol-rest");
      this.inputValue = specialIdSuffix && isNaN(this.initialValue) ? "" : this.initialValue;
      this.$emit("update:value", this.inputValue);
    },
    disabled(bool) {
      if (this.domIdSuffix !== "total-active-duration" && this.domIdSuffix !== "num-cycles") {
        this.inputValue = bool ? "" : this.initialValue;
      }
    },
  },
  methods: {
    onBFormInput: function () {
      this.$emit("update:value", this.inputValue);
    },
  },
};
</script>
<style type="text/css">
body {
  user-select: none;
}

.div__input-background {
  transform: rotate(0deg);
  box-sizing: border-box;
  padding: 0px;
  margin: 0px;
  background: rgb(17, 17, 17);
  position: absolute;
  top: 0px;
  left: 0px;
  visibility: visible;
  border: 2px solid rgb(17, 17, 17);
  border-radius: 0px;
  box-shadow: none;
  z-index: 3;
  pointer-events: all;
}

.span__input-content-label {
  pointer-events: all;
  text-align: center;
  line-height: 100%;
  transform: rotate(0deg);
  overflow: hidden;
  position: absolute;
  height: 30px;
  top: 0px;
  left: 5px;
  padding: 5px;
  visibility: visible;
  user-select: none;
  font-family: Muli;
  font-weight: normal;
  font-style: normal;
  text-decoration: none;
  font-size: 17px;
  color: rgb(183, 183, 183);
  text-align: center;
  z-index: 25;
}

.span__input-controls-content-input-txt-widget {
  padding-left: 0px;
  padding-right: 0px;
  overflow: hidden;
  white-space: nowrap;
  text-align: left;
  font-weight: normal;
  transform: translateZ(0px);
  position: absolute;
  top: 0px;
  left: 0px;
  user-select: none;
  font-family: "Anonymous Pro";
  font-style: normal;
  text-decoration: none;
  font-size: 17px;
  color: rgb(255, 255, 255);
  background-color: #2f2f2f;
}

.div__input-controls-content-widget {
  pointer-events: all;
  transform: rotate(0deg);
  overflow: hidden;
  position: absolute;
  left: 0px;
  visibility: visible;
  z-index: 7;
  background-color: #1c1c1c;
}

.div__input-controls-content-widget--invalid {
  border-width: thin;
  border-style: solid;
  border-color: #bd3532;
}

.div__input-controls-content-widget--valid {
  border-width: thin;
  border-style: solid;
  border-color: #19ac8a;
}

.div__input-controls-content-feedback {
  line-height: 1;
  transform: rotate(0deg);
  padding: 0px;
  margin: 0px;
  overflow-wrap: break-word;
  color: rgb(229, 74, 74);
  font-family: Muli;
  position: absolute;
  left: 0px;
  height: 13px;
  visibility: visible;
  user-select: none;
  text-align: left;
  font-size: 10px;
  letter-spacing: normal;
  font-weight: normal;
  font-style: normal;
  text-decoration: none;
  z-index: 17;
  pointer-events: all;
}

/* Over ride the bootstrap default color for  valid (tick) alert from #28a745 to the one matching the mockflow value #19ac8a */
.form-control.is-valid {
  background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' width='8' height='8' viewBox='0 0 8 8'%3e%3cpath fill='%2319ac8a' d='M2.3 6.73L.6 4.53c-.4-1.04.46-1.4 1.1-.8l1.1 1.4 3.4-3.8c.6-.63 1.6-.27 1.2.7l-4 4.6c-.43.5-.8.4-1.1.1z'/%3e%3c/svg%3e");
}

/* Over ride the bootstrap default color for  valid (stop exclamatory) alert from #dc3545 to the one matching the mockflow value #bd3532 */
.form-control.is-invalid {
  background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' fill='none' stroke='%23bd3532' viewBox='0 0 12 12'%3e%3ccircle cx='6' cy='6' r='4.5'/%3e%3cpath stroke-linejoin='round' d='M5.8 3.6h.4L6 6.5z'/%3e%3ccircle cx='6' cy='8.2' r='.6' fill='%23bd3532' stroke='none'/%3e%3c/svg%3e");
}
</style>
