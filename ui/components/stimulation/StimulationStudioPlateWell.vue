<template>
  <div>
    <div
      class="div__simulationstudio-plate-well-location"
      :style="computedStyle"
      @mouseenter="onEnterWell(index)"
      @mouseleave="onLeaveWell(index)"
      @click.exact="onClickExact(index)"
      @click.shift.exact="onClickShiftExact(index)"
    >
      <PlateWell
        class="well"
        :svgHeight="70"
        :svgWidth="70"
        :circleX="38"
        :circleY="35"
        :radius="26"
        :strk="stroke"
        :plateFill="protocolFill"
        :strokeWdth="strokeWdth"
        :index="index"
        :fill-opacity="fillOpacity"
      />
      <svg
        v-if="disable"
        v-b-popover.hover.top="errorMessage"
        :title="'Disabled'"
        class="svg__open-circuit-container"
        viewBox="0 0 77 77"
      >
        <path
          :style="svg_OpenCircuitOuter_DynamicClass"
          d="M30.9,3.9a27,27,0,1,1-27,27,27,27,0,0,1,27-27m0-3.9A30.9,30.9,0,1,0,61.8,30.9,30.9,30.9,0,0,0,30.9,0Z"
        />
        <path
          class="svg__open-circuit"
          d="M17.3,28.8a2,2,0,0,1,2,2.1,2,2,0,0,1-2,2,2,2,0,0,1-2.1-2,2.1,2.1,0,0,1,2.1-2.1m0-4a6.1,6.1,0,1,0,6,6.1,6.1,6.1,0,0,0-6-6.1Z"
        />
        <path
          class="svg__open-circuit"
          d="M45.3,28.8a2,2,0,0,1,2,2.1,2,2,0,0,1-2,2,2,2,0,0,1-2.1-2,2.1,2.1,0,0,1,2.1-2.1m0-4a6.1,6.1,0,1,0,6,6.1,6.1,6.1,0,0,0-6-6.1Z"
        />
        <rect class="svg__open-circuit" x="3.5" y="28.9" width="8.3" height="4" />
        <rect
          class="svg__open-circuit"
          x="18.3"
          y="22.1"
          width="19.3"
          height="4"
          transform="translate(-8.8 26.8) rotate(-45)"
        />
        <rect class="svg__open-circuit" x="50.5" y="28.9" width="8.3" height="4" />
      </svg>
      <span
        v-if="!disable"
        class="span__simulationstudio-plate-well-protocol-location"
        :style="computedLabelLeft"
      >
        {{ protocolType }}
      </span>
    </div>
  </div>
</template>
<script>
import PlateWell from "@/components/basic-widgets/PlateWell.vue";

import Vue from "vue";
import { VBPopover } from "bootstrap-vue";
Vue.directive("b-popover", VBPopover);

export default {
  name: "StimulationStudioPlateWell",
  components: {
    PlateWell,
  },
  props: {
    disable: { type: Boolean, default: false },
    stroke: { type: String, default: "" },
    protocolFill: { type: String, default: "#B7B7B7" },
    strokeWdth: { type: Number, default: 0 },
    display: { type: Boolean, default: false },
    index: {
      type: Number,
      default: 0,
      validator: (value) => {
        return value >= 0 && value < 24;
      },
    },
    errorMessage: { type: String, default: "Open circuit found" },
    protocolType: { type: String, default: "" },
  },
  computed: {
    computedTop: function () {
      return 26 + (this.index % 4) * 60;
    },
    computedLeft: function () {
      return 29 + Math.floor(this.index / 4) * 62;
    },
    computedLabelLeft: function () {
      return this.display ? "left: 29px;" : "left: 32px;";
    },
    computedStyle: function () {
      return "top:" + this.computedTop + "px;" + "left:" + this.computedLeft + "px;";
    },
    fillOpacity: function () {
      if (this.disable) return 0.3;
      else if (this.protocolType) return 0.7;
      else return 1;
    },
    svg_OpenCircuitOuter_DynamicClass: function () {
      return this.strokeWdth !== 0 ? "fill: #FFFFFF;" : "fill: rgb(228, 4, 4);";
    },
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
  },
};
</script>
<style>
.div__simulationstudio-plate-well-location {
  pointer-events: all;
  transform: rotate(0deg);
  position: absolute;
  width: 66px;
  height: 66px;
  visibility: visible;
}
.span__simulationstudio-plate-well-protocol-location {
  line-height: 100%;
  width: 20px;
  height: 20px;
  position: fixed;
  bottom: 19px;
  font-weight: bold;
  visibility: visible;
  font-family: Muli;
  color: rgb(255, 255, 255);
  cursor: pointer;
  text-shadow: -1px -1px 0 #6f7173, 1px -1px 0 #6f7173, -1px 1px 0 #6f7173, 1px 1px 0 #6f7173;
  /* creates a light outline for light protocol colors */
}
.div__popover-overlay {
  height: 50px;
  width: 50px;
  left: 15px;
  top: 10px;
  position: absolute;
}
.svg__open-circuit {
  fill: rgb(228, 4, 4);
}
.svg__open-circuit-container {
  position: relative;
  bottom: 62px;
  left: 12px;
}
</style>
