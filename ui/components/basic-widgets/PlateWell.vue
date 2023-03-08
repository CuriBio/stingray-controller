<template>
  <svg :height="svgHeight" :width="svgWidth" :index="index" style="cursor: pointer">
    <circle
      class="well"
      :cx="circleX"
      :cy="circleY"
      :r="radius"
      :stroke="strk"
      :fill="plateFill"
      :stroke-width="strokeWdth"
      @mouseenter="onEnterWell(index)"
      @mouseleave="onLeaveWell(index)"
      @click.exact="onClickExact(index)"
      @click.shift.exact="onClickShiftExact(index)"
      @click.ctrl.exact="onClickCtrlExact(index)"
    />
  </svg>
</template>
<script>
export default {
  name: "PlateWell",
  props: {
    classname: { type: String, default: "" },
    svgHeight: { type: Number, default: 0 },
    svgWidth: { type: Number, default: 0 },
    circleX: { type: Number, default: 0 },
    circleY: { type: Number, default: 0 },
    radius: { type: Number, default: 0 },
    strk: { type: String, default: "" },
    strokeWdth: { type: Number, default: 0 },
    plateFill: { type: String, default: "'#B7B7B7'" },
    index: { type: Number, default: 0 },
  },
  methods: {
    onEnterWell(index) {
      this.$emit("enter-well", index);
    },
    onLeaveWell(index) {
      this.$emit("leave-well", index);
    },
    onClickExact(index) {
      this.$emit("click-exact", index);
    },
    onClickShiftExact(index) {
      this.$emit("click-shift-exact", index);
    },
    onClickCtrlExact(index) {
      this.$emit("click-ctrl-exact", index);
    },
  },
};
</script>
<style></style>
