<template>
  <div
    class="div__small-dropdown-background"
    :style="'width: ' + inputWidthBackground + 'px;' + 'height: ' + inputHeight + 'px;'"
  >
    <div
      :id="'smallDropdown_' + domIdSuffix"
      class="div__small-dropdown-controls-content-widget"
      :style="
        'width: ' + inputWidth + 'px;' + 'top:' + inputWidgetTop + 'px;' + 'height:' + inputHeight + 'px;'
      "
      @click="!disableToggle ? toggle() : null"
    >
      <div
        class="span__small-dropdown-controls-content-input-txt-widget"
        :style="'width: ' + inputWidth + 'px;'"
      >
        <span class="span__small-controls-content-input-txt-widget">{{ chosenOption.name }}</span>
      </div>
      <div class="arrow" :class="{ expanded: visible }" />
      <div :class="{ hidden: !visible, visible }">
        <ul :style="`bottom: ${bottomPixels}px`">
          <li
            v-for="item in filteredOptions"
            :id="domIdSuffix + `_${item.id}`"
            :key="item.id"
            :value="item"
            @click="!disableSelection ? changeSelection(item.id) : null"
          >
            {{ item.name }}
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>
<script>
export default {
  name: "SmallDropDown",
  props: {
    optionsText: { type: Array, required: true },
    inputWidth: { type: Number, default: 210 },
    inputHeight: { type: Number, default: 0 },
    optionsIdx: { type: Number, default: 0 },
    domIdSuffix: { type: String, default: "" }, // for testing
    titleLabel: { type: String, default: "" },
    disableToggle: { type: Boolean, default: false },
    disableSelection: { type: Boolean, default: false },
  },
  data() {
    return {
      inputWidthBackground: this.inputWidth + 4,
      visible: false,
      optionsList: [],
    };
  },
  computed: {
    dropdownOptions: function () {
      return this.optionsText.map((option, i) => {
        return {
          id: i,
          name: option,
        };
      });
    },
    filteredOptions: function () {
      return this.dropdownOptions.filter((option) => option !== this.chosenOption);
    },
    inputWidgetTop: function () {
      return this.titleLabel !== "" ? 40 : 0;
    },
    bottomPixels: function () {
      return (this.optionsText.length - 2) * 25 + 12;
    },
    chosenOption: function () {
      return this.dropdownOptions[this.optionsIdx];
    },
  },
  watch: {
    disableToggle: function () {
      if (this.disableToggle) this.visible = false;
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
.div__small-dropdown-background {
  transform: rotate(0deg);
  margin: 0px;
  position: relative;
  top: 0px;
  left: 0px;
  margin-bottom: 7px;
  border-radius: 0px;
  box-shadow: none;
  cursor: pointer;
  z-index: 5;
}
.span__small-controls-content-input-txt-widget {
  padding-left: 10px;
  padding-right: 10px;
  white-space: nowrap;
  transform: translateZ(0px);
  position: absolute;
  height: 25px;
  line-height: 25px;
  top: 0px;
  left: 0px;
  user-select: none;
  font-family: Muli;
  font-size: 11px;
  color: #b7b7b7;
  background-color: #1c1c1c;
}
.div__small-dropdown-controls-content-widget {
  transform: rotate(0deg);
  position: absolute;
  background-color: #1c1c1c;
  font-family: Muli;
  padding: 8px;
}
.arrow {
  position: absolute;
  right: 10px;
  top: 43%;
  border-left: 4px solid transparent;
  border-right: 4px solid transparent;
  border-top: 6px solid #888;
  transform: rotateZ(0deg) translateY(0px);
  transition-duration: 0.3s;
  transition-timing-function: cubic-bezier(0.59, 1.39, 0.37, 1.01);
}
.expanded {
  transform: rotateZ(180deg) translateY(2px);
}
ul {
  width: 100%;
  list-style-type: none;
  padding: 0;
  left: 0;
  font-size: 11px;
  height: 25px;
  line-height: 25px;
  position: absolute;
  color: #b7b7b7;
  z-index: 5;
}

li {
  color: #b7b7b7;
  background-color: #292929;
  padding-left: 10px;
  padding-right: 10px;
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
</style>
