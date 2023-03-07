<template>
  <div>
    <div class="div__button-background" :style="backgroundCssprops">
      <span
        v-for="btnIndex in numOfBtn"
        :key="btnIndex"
        :ref="btnIndex.toString()"
        class="span__button-label"
        :style="btnStateprop(btnIndex)"
        @click="selected(btnIndex)"
        @mouseenter="hoverActive(btnIndex)"
        @mouseleave="hoverInactive(btnIndex)"
        >{{ buttonNames[btnIndex - 1] }}
      </span>
    </div>
    <div v-if="numOfVerticalline >= 1">
      <canvas
        v-for="lineIndex in numOfVerticalline"
        :key="lineIndex"
        class="canvas__vertical-line"
        :style="btnDividerDisplay(lineIndex)"
      >
      </canvas>
    </div>
    <canvas class="canvas__common-horizontal-line" :style="'width: ' + (buttonWidgetWidth - 10) + 'px;'">
    </canvas>
  </div>
</template>
<script>
export default {
  name: "ButtonWidget",
  props: {
    buttonNames: {
      type: Array,
      required: true,
    },
    enabledColor: { type: String, default: "#FFFFFF" },
    disabledColor: { type: String, default: "#3F3F3F" },
    hoverColor: {
      type: Array,
      required: true,
    },
    isEnabled: {
      type: Array,
      default: function () {
        return new Array(this.buttonNames.length).fill(true);
      },
    },
    buttonWidgetWidth: { type: Number, default: 0 },
    buttonWidgetHeight: { type: Number, default: 0 },
    buttonWidgetTop: { type: Number, default: 0 },
    buttonWidgetLeft: { type: Number, default: 0 },
    buttonBackgroundColor: { type: String, default: "rgb(17, 17, 17)" },
  },
  computed: {
    numOfBtn: function () {
      return this.buttonNames.length;
    },
    numOfVerticalline: function () {
      return this.buttonNames.length - 1;
    },
    backgroundCssprops: function () {
      return (
        "width: " +
        this.buttonWidgetWidth +
        "px; height: " +
        this.buttonWidgetHeight +
        "px; top: " +
        this.buttonWidgetTop +
        "px; left: " +
        this.buttonWidgetLeft +
        "px; background: " +
        this.buttonBackgroundColor
      );
    },
  },
  methods: {
    btnStateprop(value) {
      const count = value - 1;
      const computedWidth = this.buttonWidgetWidth / this.numOfBtn;
      const computedLeft = computedWidth * count;
      return this.isEnabled[count]
        ? "color: " +
            this.enabledColor +
            ";" +
            "width: " +
            computedWidth +
            "px;" +
            "left: " +
            computedLeft +
            "px;" +
            "cursor: pointer;"
        : "color: " +
            this.disabledColor +
            ";" +
            "width: " +
            computedWidth +
            "px;" +
            "left: " +
            computedLeft +
            "px;";
    },
    btnDividerDisplay(value) {
      const computedWidth = this.buttonWidgetWidth / this.numOfBtn;
      const leftShift = computedWidth * value;
      return "left: " + leftShift + "px;";
    },
    selected(value) {
      if (this.isEnabled[value - 1]) {
        this.$emit("btn-click", value - 1);
      }
    },
    hoverActive(value) {
      if (this.isEnabled[value - 1]) {
        const localRef = this.$refs[value.toString()];
        localRef[0].style.color = this.hoverColor[value - 1];
      }
    },
    hoverInactive(value) {
      if (this.isEnabled[value - 1]) {
        const localRef = this.$refs[value.toString()];
        localRef[0].style.color = this.enabledColor;
      }
    },
  },
};
</script>
<style>
body {
  user-select: none;
}
.div__button-background {
  transform: rotate(0deg);
  box-sizing: border-box;
  padding: 0px;
  margin: 0px;
  display: flex;
  justify-content: center;
  align-items: center;
  position: absolute;
  visibility: visible;
  border: 2px solid rgb(0, 0, 0);
  border-radius: 0px;
  box-shadow: none;
  z-index: 3;
  pointer-events: all;
  overflow: hidden;
}

.span__button-label {
  pointer-events: all;
  line-height: 100%;
  transform: rotate(0deg);
  overflow: hidden;
  position: absolute;
  height: 30px;
  padding: 5px;
  visibility: visible;
  user-select: none;
  font-family: Muli;
  font-weight: normal;
  font-style: normal;
  text-decoration: none;
  font-size: 17px;
  color: #3f3f3f;
  text-align: center;
  z-index: 3;
}

.canvas__vertical-line {
  transform: rotate(0deg);
  pointer-events: all;
  position: absolute;
  width: 2px;
  height: 50px;
  top: 0px;
  left: 0px;
  visibility: visible;
  z-index: 3;
  background-color: #3f3f3f;
  opacity: 0.5;
}

.canvas__common-horizontal-line {
  transform: rotate(0deg);
  pointer-events: all;
  position: absolute;
  height: 2px;
  top: 0px;
  left: 5px;
  visibility: visible;
  z-index: 3;
  background-color: #3f3f3f;
  opacity: 0.5;
}
</style>
