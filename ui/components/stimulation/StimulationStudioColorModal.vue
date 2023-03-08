<template>
  <div class="div__color-modal-container">
    Select color:
    <div class="div__container-color-block">
      <div
        v-for="color in colorSelection"
        :id="color"
        :key="color"
        class="individual-color-block"
        :style="'background-color: ' + color"
        @click="handleColorSelection"
      />
    </div>
    <div class="div__color-button-container">
      <ButtonWidget
        :id="'button-widget-id'"
        :buttonWidgetWidth="202"
        :buttonWidgetHeight="40"
        :buttonWidgetTop="0"
        :buttonWidgetLeft="0"
        :buttonBackgroundColor="'#292929'"
        :buttonNames="['Cancel']"
        :hoverColor="['#bd4932']"
        @btn-click="handleColorSelection"
      />
    </div>
  </div>
</template>
<script>
import ButtonWidget from "@/components/basic-widgets/ButtonWidget.vue";

export default {
  name: "StimulationStudioColorModal",
  components: {
    ButtonWidget,
  },
  props: {
    currentColor: {
      type: String,
      required: true,
    },
  },
  computed: {
    colorSelection: function () {
      const nonGreenRanges = [...Array(71).keys(), ...[...Array(360).keys()].splice(170)];

      return nonGreenRanges.filter((hue) => hue % 23 === 0).map((hue) => `hsla(${hue}, 100%, 50%, 1)`);
    },
  },
  methods: {
    handleColorSelection({ target }) {
      const colorToEmit = !target ? this.currentColor : target.id;
      this.$emit("change-pulse-color", colorToEmit);
    },
  },
};
</script>
<style>
.div__color-modal-container {
  height: 200px;
  width: 200px;
  background: #292929;
  color: rgb(255, 255, 255);
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
  padding: 5px 10px;
  border-radius: 4px;
}

.div__container-color-block {
  height: 150px;
  width: 160px;
  margin: 5px;
  display: grid;
  grid-template-areas:
    "0 1 2 3"
    "4 5 6 7"
    "8 9 10 11";
}
.individual-color-block {
  border: 1px solid #292929;
}
.individual-color-block:hover {
  border: 2px solid white;
  cursor: pointer;
}
.div__color-button-container {
  width: 202;
  height: 40px;
  top: 213px;
  left: 15px;
  position: absolute;
}
</style>
