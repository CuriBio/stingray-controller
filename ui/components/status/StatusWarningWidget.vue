<template>
  <div>
    <div class="div__status-warning-background" :style="`height: ${dynamicModalHeight}px;`">
      <span class="span__status-warning-label">{{ modalLabels.header }}</span>
      <div ref="messageArea" class="span__status-warning-message">
        <p id="p__statusWarningsg1">{{ modalLabels.msgOne }}</p>
        <p v-show="!includeFilepath">
          {{ modalLabels.msgTwo }}
          <a
            v-if="emailError"
            id="errorContact"
            href="mailto:support@curibio.com ? subject = Short circuit error"
            >support@curibio.com</a
          >
        </p>
        <textarea
          v-show="includeFilepath"
          ref="textarea"
          class="textarea__upload-file-path"
          spellcheck="false"
          :value.prop="modalLabels.msgTwo"
          :rows="computeNumberOfRows"
          :cols="50"
          :disabled="true"
          :style="`height: ${textareaDynamicHeight}`"
        />
      </div>
      <div class="div__status-warning-button" :style="`top: ${dynamicModalHeight}px;`">
        <ButtonWidget
          :buttonWidgetWidth="420"
          :buttonWidgetHeight="50"
          :buttonWidgetTop="0"
          :buttonWidgetLeft="0"
          :buttonNames="modalLabels.buttonNames"
          :enabledColor="'#B7B7B7'"
          :hoverColor="['#bd4932', '#19ac8a', '#19ac8a']"
          @btn-click="handleClick"
        />
      </div>
    </div>
  </div>
</template>
<script>
import ButtonWidget from "@/components/basic-widgets/ButtonWidget.vue";

export default {
  name: "StatusWarningWidget",
  components: {
    ButtonWidget,
  },
  props: {
    modalLabels: {
      type: Object,
      default() {
        return {
          header: "Warning!",
          msgOne: "Operations are still in progress.",
          msgTwo: "Are you sure you want to exit?",
          buttonNames: ["Cancel", "Yes"],
        };
      },
    },
    emailError: {
      type: Boolean,
      default: false,
    },
    includeFilepath: {
      type: Boolean,
      default: false,
    },
  },
  computed: {
    textareaDynamicHeight: function () {
      return this.computeNumberOfRows * 18 + 25;
    },
    computeNumberOfRows: function () {
      return Math.ceil(((this.modalLabels.msgTwo.length * 1.0) / 40).toFixed(1));
    },
    dynamicModalHeight: function () {
      const msgRows = Math.ceil(
        ((this.modalLabels.msgOne.length + this.modalLabels.msgTwo.length) / 50).toFixed(1)
      );
      return msgRows * 18 + 125;
    },
  },

  methods: {
    handleClick: function (idx) {
      this.$emit("handle-confirmation", idx);
    },
  },
};
</script>
<style scoped>
.div__status-warning-background {
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
.span__status-warning-label {
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
.span__status-warning-message {
  line-height: 1.2;
  transform: rotate(0deg);
  padding: 0px;
  margin: 0px;
  overflow-wrap: break-word;
  color: rgb(183, 183, 183);
  font-family: Muli;
  position: absolute;
  top: 65px;
  left: 21px;
  width: 378px;
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
.div__status-warning-button {
  left: 0px;
  position: absolute;
}
.textarea__upload-file-path {
  line-height: 1.2;
  transform: rotate(0deg);
  padding: 0px;
  margin: 0px;
  word-wrap: break-word;
  outline: none;
  color: rgb(183, 183, 183);
  font-family: Courier New;
  position: absolute;
  left: 15px;
  width: 338px;
  background: rgb(17, 17, 17);
  border: 2px solid rgb(17, 17, 17);
  border-radius: 0px;
  box-shadow: none;
  overflow: hidden;
  visibility: visible;
  user-select: none;
  vertical-align: top;
  text-align: center;
  font-size: 15px;
  letter-spacing: normal;
  font-weight: normal;
  font-style: normal;
  text-decoration: none;
  resize: none;
  z-index: 5;
  pointer-events: all;
}

#errorContact {
  color: rgb(183, 183, 183);
}
</style>
