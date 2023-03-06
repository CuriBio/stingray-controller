<template>
  <div>
    <div class="div__status-error-catch-background" :style="errorBackgroundCssprops" />
    <span class="div_status-error-catch-title-label">An&nbsp;<wbr />error&nbsp;<wbr />occurred. </span>
    <div class="div_status-error-catch-alert-txt" :style="errorCatchAlert">
      <p>{{ shutdownErrorMessage }}</p>
      <textarea
        v-if="installerLink"
        class="textarea__installer-link"
        name="errorFile"
        :rows="2"
        cols="75"
        spellcheck="false"
        :value.prop="installerLink"
        :disabled="true"
      />
    </div>
    <div class="div_status-email-txt" :style="emailTextCssprops">
      <p>
        Please send the folder shown below to
        <a id="errorContact" href="mailto:support@curibio.com ? subject = Mantarray Error log"
          >support@curibio.com</a
        >
      </p>
    </div>
    <textarea
      class="textarea__error-file-path"
      name="errorFile"
      :rows="computeNumberOfRows"
      cols="50"
      spellcheck="false"
      :value.prop="logFilepath"
      :disabled="true"
      :style="textarea__errorCssprops"
    />
    <div class="div_status-error-catch-next-step-txt" :style="nextStepCssprops">
      <p>
        Please turn the instrument off, unplug from the PC,<br />
        and then wait 10 seconds before attempting to use again.
      </p>
    </div>
    <div class="div__error-button" :style="errorCatchButtonCssprops">
      <ButtonWidget
        :buttonWidgetWidth="450"
        :buttonWidgetHeight="50"
        :buttonWidgetTop="0"
        :buttonWidgetLeft="0"
        :buttonNames="['Okay']"
        :enabledColor="'#B7B7B7'"
        :hoverColor="['#FFFFFF']"
        @btn-click="processOk"
      >
      </ButtonWidget>
    </div>
  </div>
</template>
<script>
import ButtonWidget from "@/components/basic-widgets/ButtonWidget.vue";
import { mapState } from "vuex";
export default {
  name: "ErrorCatchWidget",
  components: {
    ButtonWidget,
  },
  props: {
    logFilepath: { type: String, default: "" },
  },
  computed: {
    ...mapState("settings", ["shutdownErrorMessage", "installerLink"]),
    computeNumberOfRows: function () {
      return Math.ceil(((this.logFilepath.length * 1.0) / 30).toFixed(1));
    },
    errorBackgroundCssprops: function () {
      let height = 250 + this.computeNumberOfRows * 12;
      if (this.installerLink) {
        height += 25;
      }
      return `height: ${height}px;`;
    },
    errorCatchAlert: function () {
      const height = this.installerLink ? 130 : 75;
      return `height: ${height}px;`;
    },
    textarea__errorCssprops: function () {
      const top = this.installerLink ? 195 : 145;
      return `height: ${25 + this.computeNumberOfRows * 12}px; top: ${top}px;`;
    },
    nextStepCssprops: function () {
      let top = 180 + this.computeNumberOfRows * 12;
      if (this.installerLink) {
        top += 35;
      }
      return `top: ${top}px;`;
    },
    errorCatchButtonCssprops: function () {
      let top = 250 + this.computeNumberOfRows * 12;
      if (this.installerLink) {
        top += 25;
      }
      return `top: ${top}px; left: 0px; position: absolute`;
    },
    emailTextCssprops: function () {
      const top = this.installerLink ? 175 : 107;
      return `top: ${top}px`;
    },
  },
  methods: {
    processOk: function () {
      this.$emit("ok-clicked");
    },
  },
};
</script>
<style>
a:link {
  color: #b7b7b7;
  background-color: transparent;
  text-decoration: none;
}
a:hover {
  color: #ffffff;
  background-color: transparent;
  text-decoration: none;
}

.div__status-error-catch-background {
  pointer-events: all;
  transform: rotate(0deg);
  position: absolute;
  background: rgb(17, 17, 17);
  width: 450px;
  top: 0px;
  left: 0px;
  visibility: visible;
  z-index: 1;
}

.div_status-error-catch-title-label {
  pointer-events: all;
  line-height: 100%;
  transform: rotate(0deg);
  overflow: hidden;
  position: absolute;
  width: 450px;
  height: 30px;
  top: 17.3852px;
  left: 0px;
  padding: 5px;
  visibility: visible;
  user-select: none;
  font-family: Muli;
  font-weight: normal;
  font-style: normal;
  text-decoration: none;
  font-size: 17px;
  color: rgb(255, 255, 255);
  text-align: center;
  z-index: 3;
}
.div_status-error-catch-alert-txt {
  line-height: 1.2;
  transform: rotate(0deg);
  padding: 0px;
  margin: 0px;
  overflow-wrap: break-word;
  color: rgb(183, 183, 183);
  font-family: Muli;
  position: absolute;
  top: 57.6407px;
  left: 0px;
  width: 450px;
  overflow: hidden;
  visibility: visible;
  user-select: none;
  text-align: center;
  font-size: 15px;
  letter-spacing: normal;
  font-weight: normal;
  font-style: normal;
  text-decoration: none;
  z-index: 5;
  pointer-events: all;
}
.div_status-email-txt {
  line-height: 1.2;
  transform: rotate(0deg);
  padding: 0px;
  margin: 0px;
  overflow-wrap: break-word;
  color: rgb(183, 183, 183);
  font-family: Muli;
  position: absolute;
  left: 0px;
  width: 450px;
  overflow: hidden;
  visibility: visible;
  user-select: none;
  text-align: center;
  font-size: 15px;
  letter-spacing: normal;
  font-weight: normal;
  font-style: normal;
  text-decoration: none;
  z-index: 5;
  pointer-events: all;
}

.textarea__error-file-path {
  line-height: 1.2;
  transform: rotate(0deg);
  padding: 0px;
  margin: 0px;
  word-break: break-all;
  outline: none;
  color: rgb(183, 183, 183);
  font-family: Courier New;
  position: absolute;
  left: 56px;
  width: 338px;
  background: rgb(17, 17, 17);
  border: 2px solid rgb(17, 17, 17);
  border-radius: 0px;
  box-shadow: none;
  overflow: hidden;
  visibility: visible;
  user-select: none;
  vertical-align: top;
  text-align: left;
  font-size: 15px;
  letter-spacing: normal;
  font-weight: normal;
  font-style: normal;
  text-decoration: none;
  resize: none;
  z-index: 5;
  pointer-events: all;
}

.textarea__installer-link {
  line-height: 1.2;
  transform: rotate(0deg);
  padding: 0px;
  margin: 0px;
  word-break: break-all;
  outline: none;
  color: rgb(183, 183, 183);
  font-family: Courier New;
  position: absolute;
  top: 59px;
  left: 20px;
  width: 406px;
  background: rgb(17, 17, 17);
  border: 2px solid rgb(17, 17, 17);
  border-radius: 0px;
  box-shadow: none;
  overflow: hidden;
  visibility: visible;
  user-select: none;
  vertical-align: top;
  text-align: left;
  font-size: 15px;
  letter-spacing: normal;
  font-weight: normal;
  font-style: normal;
  text-decoration: none;
  resize: none;
  z-index: 5;
  pointer-events: all;
}

.div_status-error-catch-next-step-txt {
  line-height: 1.2;
  transform: rotate(0deg);
  padding: 0px;
  margin: 0px;
  overflow-wrap: break-word;
  color: rgb(183, 183, 183);
  font-family: Muli;
  position: absolute;
  left: 0px;
  width: 450px;
  height: 66px;
  overflow: hidden;
  visibility: visible;
  user-select: none;
  text-align: center;
  font-size: 15px;
  letter-spacing: normal;
  font-weight: normal;
  font-style: normal;
  text-decoration: none;
  z-index: 5;
  pointer-events: all;
}
</style>
