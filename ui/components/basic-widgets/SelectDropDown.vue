<template>
  <div class="div__select-dropdown-background" :style="dynamicBackgroundStyle">
    <span
      v-if="titleLabel !== ''"
      class="span__select-dropdown-content-label"
      :style="'width: ' + inputWidth + 'px;'"
    >
      {{ titleLabel }}
    </span>
    <div
      class="div__select-dropdown-controls-content-widget"
      :style="dynamicContentWidgetStyle"
      @click="toggle()"
    >
      <div
        class="span__select-dropdown-controls-content-input-txt-widget"
        :style="'width: ' + inputWidth + 'px;'"
      >
        <div class="div__chosen-option-container">
          <span class="span__input-controls-content-dropdown-widget">
            <span :style="'color:' + chosenOption.color">{{ chosenOption.letter }}</span>
            {{ chosenOption.name }}</span
          >
        </div>
      </div>
      <div class="arrow" :class="{ expanded: visible }" />
      <div :class="{ hidden: !visible, visible }">
        <ul>
          <li v-for="item in filteredOptions" :key="item.id" :value="item" @click="changeSelection(item.id)">
            <span :style="'color:' + item.color">{{ item.letter }}</span
            >{{ item.name }}
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>
<script>
export default {
  name: "SelectDropDown",
  props: {
    titleLabel: { type: String, default: "" }, // titleText (str) (optional, defaults to empty string "")
    value: { type: String, default: "" }, // fieldValue (str) (optional, defaults to empty string "")
    optionsText: { type: Array, required: true },
    inputWidth: { type: Number, default: 210 },
    optionsIdx: { type: Number, default: 0 },
    inputHeight: { type: Number, default: 0 }, // This prop is utilized by the parent component
  },
  data() {
    return {
      inputWidthBackground: this.inputWidth + 4,
      visible: false,
    };
  },
  computed: {
    inputHeightBackground: function () {
      return this.titleLabel !== "" ? 100 : 60;
    },
    inputWidgetTop: function () {
      return this.titleLabel !== "" ? 40 : 0;
    },
    dynamicBackgroundStyle: function () {
      return "width: " + this.inputWidthBackground + "px;" + "height: " + this.inputHeightBackground + "px;";
    },
    dynamicContentWidgetStyle: function () {
      return (
        "width: " +
        this.inputWidth +
        "px;" +
        "top:" +
        this.inputWidgetTop +
        "px;" +
        "height:" +
        this.inputHeight +
        "px;"
      );
    },
    dropdownOptions: function () {
      return this.optionsText.map((option, i) => {
        return typeof option === "string"
          ? {
              id: i,
              name: option,
            }
          : {
              id: i,
              name: option.label,
              letter: option.letter + " ",
              color: option.color,
            };
      });
    },
    filteredOptions: function () {
      return this.dropdownOptions.filter((option) => option !== this.chosenOption);
    },
    chosenOption: function () {
      return this.dropdownOptions[this.optionsIdx];
    },
  },
  methods: {
    changeSelection(idx) {
      this.$emit("selection-changed", idx);
    },
    toggle() {
      this.visible = !this.visible;
    },
  },
};
</script>
<style scoped>
body {
  user-select: none;
}
.div__select-dropdown-background {
  transform: rotate(0deg);
  padding: 0px;
  margin: 0px;
  position: absolute;
  top: 0px;
  left: 0px;
  border-radius: 0px;
  box-shadow: none;
  cursor: pointer;
}
.span__select-dropdown-content-label {
  pointer-events: all;
  line-height: 100%;
  transform: rotate(0deg);
  position: absolute;
  height: 30px;
  top: 0px;
  left: 0px;
  padding: 5px;
  user-select: none;
  font-family: Muli;
  font-size: 19px;
  color: rgb(255, 255, 255);
  text-align: center;
  cursor: pointer;
}
.span__input-controls-content-dropdown-widget {
  padding-left: 10px;
  padding-right: 10px;
  white-space: nowrap;
  transform: translateZ(0px);
  position: absolute;
  height: 45px;
  top: 0px;
  left: 0px;
  user-select: none;
  font-family: Muli;
  font-size: 15px;
  color: #b7b7b7;
  background-color: #1c1c1c;
}
.div__select-dropdown-controls-content-widget {
  pointer-events: all;
  transform: rotate(0deg);
  position: absolute;
  left: 0px;
  background-color: #1c1c1c;
  font-family: Muli;
  padding: 10px;
}
.arrow {
  position: absolute;
  right: 10px;
  top: 40%;
  width: 0;
  height: 0;
  border-left: 5px solid transparent;
  border-right: 5px solid transparent;
  border-top: 7px solid #888;
  transform: rotateZ(0deg) translateY(0px);
  transition-duration: 0.3s;
  transition-timing-function: cubic-bezier(0.59, 1.39, 0.37, 1.01);
}
.expanded {
  transform: rotateZ(180deg) translateY(2px);
  overflow: hidden;
  overflow: hidden;
  visibility: visible;
  z-index: 100;
}
ul {
  width: 100%;
  list-style-type: none;
  padding: 0;
  margin-top: 17px;
  left: 0;
  font-size: 16px;
  position: absolute;
  color: #b7b7b7;
  border-top: 1px solid rgb(17, 17, 17);
}
li {
  padding: 12px;
  color: #b7b7b7;
  background-color: #292929;
  overflow: hidden;
}
li:hover {
  background: #1c1c1c;
}
.current {
  color: #b7b7b7;
  background-color: #1c1c1c;
  visibility: hidden;
}
.hidden {
  visibility: hidden;
}
.visible {
  visibility: visible;
}
.div__chosen-option-container {
  width: 255px;
  height: 20px;
  line-height: 1.5;
  overflow: hidden;
  position: relative;
}
</style>
