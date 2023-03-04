<template>
  <div class="div__input-dropdown-background" :style="dynamicContainerStyles">
    <span
      v-if="titleLabel !== ''"
      class="span__input-dropdown-content-label"
      :style="'width: ' + inputWidth + 'px;'"
    >
      {{ titleLabel }}
      <!--  original mockflow ID: cmpDb072c1da7a823374cbee04cb1666edb1   -->
    </span>

    <div
      class="div__input-dropdown-controls-content-widget"
      :class="[
        messageIfInvalid
          ? 'div__input-dropdown-controls-content-widget--invalid'
          : 'div__input-dropdown-controls-content-widget--valid'
      ]"
      :style="'width: ' + inputWidth + 'px;' + 'top:' + inputWidgetTop + 'px;'"
    >
      <span
        class="span__input-dropdown-controls-content-input-txt-widget"
        :style="'width: ' + inputWidth + 'px;'"
      >
        <b-form-input
          :id="'input-dropdown-widget-' + optionsId"
          v-model="inputDropdownValueKey"
          :list="'option-list' + optionsId"
          :placeholder="placeholder"
          :disabled="disabled"
          class="w-100 h-100 edit-id"
          :style="`border-radius: 0; background-color: ${inputBackgroundColor}; border: 0px; color: #ffffff`"
        ></b-form-input>
        <datalist v-if="dropdownOptions.length" :id="'option-list' + optionsId">
          <option v-for="item in dropdownOptions" :id="item.id" :key="item.id">
            {{ item.name }}
          </option>
        </datalist>
      </span>
    </div>
    <div
      v-show="messageIfInvalid"
      :id="'input-dropdown-widget-feedback-' + optionsId"
      class="div__input-dropdown-controls-content-feedback"
      :style="'width: ' + inputWidth + 'px;' + 'top:' + inputFeedbackTop + 'px;'"
    >
      {{ invalidText }}
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
export default {
  name: "InputDropDown",
  props: {
    titleLabel: { type: String, default: "" }, // titleText (str) (optional, defaults to empty string "")
    placeholder: { type: String, default: "" }, // placeholder (str)
    invalidText: { type: String, default: "" }, // invalidText (str)
    value: { type: String, default: "" }, // fieldValue (str) (optional, defaults to empty string "")
    inputWidth: { type: Number, default: 0 }, // textboxWidth (int)  [pixels]
    disabled: { type: Boolean, default: false }, // disabled (optional bool=False) (not able to type into input)
    optionsText: { type: Array, required: true },
    optionsId: { type: String, default: "" }, // This prop is utilized by the parent component
    messageIfInvalid: { type: Boolean, default: false }, // when set to true, will display a simple feedback
    inputBackgroundColor: { type: String, default: "#1c1c1c" },
    containerBackgroundColor: { type: String, default: "rgb(0, 0, 0)" }
  },
  data() {
    return {
      inputDropdownValueKey: this.value,
      inputWidthBackground: this.inputWidth + 4
    };
  },
  computed: {
    dropdownOptions: function() {
      return this.optionsText.map((option, i) => {
        // the optionsText is required true so a minimum of one element is needed
        // if suppose optionsText.length is zero(0) then return doesn't change its []
        return {
          id: this.optionsId + i,
          name: option
        };
      });
    },
    inputHeightBackground: function() {
      return this.titleLabel !== "" ? 100 : 60;
    },
    inputWidgetTop: function() {
      return this.titleLabel !== "" ? 40 : 0;
    },
    inputFeedbackTop: function() {
      return this.titleLabel !== "" ? 88 : 48;
    },
    dynamicContainerStyles: function() {
      return (
        "width: " +
        this.inputWidthBackground +
        "px;" +
        "height: " +
        this.inputHeightBackground +
        "px; background: " +
        this.containerBackgroundColor +
        "; border: 2px solid " +
        this.containerBackgroundColor +
        ";"
      );
    }
  },
  watch: {
    inputDropdownValueKey: function() {
      this.$emit("update:value", this.inputDropdownValueKey);
    },
    value: function() {
      this.inputDropdownValueKey = this.value;
    }
  },
  methods: {}
};
</script>
<style scoped>
body {
  user-select: none;
}
.div__input-dropdown-background {
  transform: rotate(0deg);
  box-sizing: border-box;
  padding: 0px;
  margin: 0px;
  position: absolute;
  top: 0px;
  left: 0px;
  visibility: visible;
  border-radius: 0px;
  box-shadow: none;
  z-index: 3;
  pointer-events: all;
}

.span__input-dropdown-content-label {
  pointer-events: all;
  line-height: 100%;
  transform: rotate(0deg);
  overflow: hidden;
  position: absolute;
  height: 30px;
  top: 0px;
  left: -15px;
  padding: 5px;
  visibility: visible;
  user-select: none;
  font-family: Muli;
  font-weight: normal;
  font-style: normal;
  text-decoration: none;
  font-size: 19px;
  color: rgb(255, 255, 255);
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
  height: 45px;
  line-height: 45px;
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

.div__input-dropdown-controls-content-widget {
  pointer-events: all;
  transform: rotate(0deg);
  overflow: hidden;
  position: absolute;
  height: 45px;
  left: 0px;
  visibility: visible;
  z-index: 7;
  background-color: #1c1c1c;
}

.div__input-dropdown-controls-content-widget--invalid {
  border-width: thin;
  border-style: solid;
  border-color: #bd3532;
}

.div__input-dropdown-controls-content-widget--valid {
  border-width: thin;
  border-style: solid;
  border-color: #19ac8a;
}

.div__input-dropdown-controls-content-feedback {
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
  overflow: hidden;
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
</style>
