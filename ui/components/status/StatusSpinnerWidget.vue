<template>
  <div>
    <div class="div__status-spinner-background" :style="modalHeight">
      <span class="span__status-spinner-label">{{ modalLabels.header }}</span>
      <div class="span__status-spinner-message" :style="messageHeight">
        <p>{{ modalLabels.msgOne }}</p>
        <p>{{ modalLabels.msgTwo }}</p>
      </div>
      <span class="span__status-spinner" :style="spinnerTop">
        <FontAwesomeIcon :icon="['fa', 'spinner']" pulse />
      </span>
    </div>
  </div>
</template>
<script>
import { library } from "@fortawesome/fontawesome-svg-core";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import { faSpinner } from "@fortawesome/free-solid-svg-icons";

library.add(faSpinner);

export default {
  name: "StatusSpinnerWidget",
  components: { FontAwesomeIcon },
  props: {
    modalLabels: {
      type: Object,
      default() {
        return {
          header: "Important!",
          msgOne: "The firmware update is in progress. It will take about 7 minutes to complete.",
          msgTwo: "Do not close the Stingray software or power off the Stingray instrument.",
        };
      },
    },
  },
  computed: {
    computeNumberOfRows: function () {
      return (
        Math.ceil(((this.modalLabels.msgOne.length * 1.0) / 40 + 1).toFixed(1)) +
        Math.ceil(((this.modalLabels.msgTwo.length * 1.0) / 40 + 1).toFixed(1))
      );
    },
    modalHeight: function () {
      return `height: ${200 + this.computeNumberOfRows * 12}px;`;
    },
    messageHeight: function () {
      return `height: ${60 + this.computeNumberOfRows * 12}px;`;
    },
    spinnerTop: function () {
      return `top: ${110 + this.computeNumberOfRows * 12}px;`;
    },
  },
};
</script>
<style scoped>
.div__status-spinner-background {
  pointer-events: all;
  transform: rotate(0deg);
  position: absolute;
  width: 420px;
  top: 0;
  left: 0;
  visibility: visible;
  color: #1c1c1c;
  border-color: #000000;
  background: rgb(17, 17, 17);
  z-index: 3;
}
.span__status-spinner-label {
  pointer-events: all;
  line-height: 100%;
  transform: rotate(0deg);
  overflow: hidden;
  position: absolute;
  width: 420px;
  height: 30px;
  top: 22.385px;
  left: 0px;
  visibility: visible;
  user-select: none;
  font-family: Muli;
  font-weight: normal;
  font-style: normal;
  text-decoration: none;
  font-size: 17px;
  color: rgb(255, 255, 255);
  text-align: center;
}
.span__status-spinner-message {
  line-height: 1.2;
  transform: rotate(0deg);
  padding: 0px;
  margin: 0px;
  overflow-wrap: break-word;
  color: rgb(183, 183, 183);
  font-family: Muli;
  position: absolute;
  top: 55px;
  left: 21px;
  width: 378px;
  overflow: hidden;
  visibility: visible;
  user-select: none;
  text-align: center;
  font-size: 15px;
  letter-spacing: normal;
  font-weight: normal;
  font-style: normal;
  text-decoration: none;
  pointer-events: all;
}
.span__status-spinner {
  left: 177px;
  position: absolute;
}
.fa-pulse {
  font-size: 4em;
  color: grey;
}
</style>
