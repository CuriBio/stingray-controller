<template>
  <div>
    <div class="div__addUser-form-controls" />
    <span class="span__addUser-form-controls-content-title"> Add&nbsp;<wbr />New&nbsp;<wbr />User </span>
    <div id="customerId" style="top: 50px; left: 50px; position: absolute; z-index: 24">
      <InputWidget
        :titleLabel="'Enter Customer ID'"
        :placeholder="'ba86b8f0-6fdf-4944-87a0-8a491a19490e'"
        :invalidText="errorTextId"
        :spellcheck="false"
        :inputWidth="400"
        :domIdSuffix="'customer-id'"
        :initialValue="storedCustomerId"
        @update:value="onUpdateId($event)"
      />
    </div>

    <div id="userName" style="top: 184px; left: 50px; position: absolute; z-index: 23">
      <span class="span__input-user-title">Enter&nbsp;<wbr />Username</span>
      <InputDropDown
        :placeholder="'Curi Bio User'"
        :invalidText="errorTextUserName"
        :inputWidth="400"
        :optionsText="storedUsernames"
        :messageIfInvalid="errorTextUserName != ''"
        :optionsId="'username'"
        :inputBackgroundColor="'rgb(63, 63, 63)'"
        :containerBackgroundColor="'#111'"
        :value.sync="userName"
        @update:value="onUpdateUserName($event)"
      />
    </div>
    <div id="pass-key" style="top: 241px; left: 50px; position: absolute; z-index: 22">
      <InputWidget
        :titleLabel="'Enter Password'"
        :placeholder="'2VSckkBYr2An3dqHEyfRRE'"
        :invalidText="errorTextPass"
        :spellcheck="false"
        :inputWidth="400"
        :type="'password'"
        :domIdSuffix="'passkey-id'"
        @update:value="onUpdatePass($event)"
      />
    </div>
    <div style="top: 350px; left: 0px; position: absolute">
      <ButtonWidget
        :buttonWidgetWidth="500"
        :buttonWidgetHeight="50"
        :buttonWidgetTop="0"
        :buttonWidgetLeft="0"
        :buttonNames="['Cancel', 'Save ID']"
        :hoverColor="['#bd4932', '#19ac8a']"
        :isEnabled="enablelistAddUser"
        @btn-click="clickedButton"
      >
      </ButtonWidget>
    </div>
  </div>
</template>
<script>
import Vue from "vue";
import { mapState } from "vuex";
import BootstrapVue from "bootstrap-vue";
import { BButton } from "bootstrap-vue";
import { BFormInput } from "bootstrap-vue";
import InputWidget from "@/components/basic-widgets/InputWidget.vue";
import ButtonWidget from "@/components/basic-widgets/ButtonWidget.vue";
import { TextValidation } from "@/js-utils/TextValidation.js";
Vue.use(BootstrapVue);
Vue.component("BFormInput", BFormInput);
Vue.component("BButton", BButton);
import "bootstrap/dist/css/bootstrap.min.css";
const TextValidation_User = new TextValidation("user_account_input");
import InputDropDown from "@/components/basic-widgets/InputDropDown.vue";

export default {
  name: "AddUser",
  components: {
    InputWidget,
    ButtonWidget,
    InputDropDown,
  },
  data() {
    return {
      customerId: "",
      userPassword: "",
      userName: "",
      errorTextId: "This field is required",
      errorTextPass: "This field is required",
      errorTextUserName: "This field is required",
      enablelistAddUser: [true, false],
    };
  },
  computed: {
    ...mapState("settings", ["storedCustomerId", "storedUsernames"]),
  },
  created: function () {
    if (this.storedCustomerId) this.onUpdateId(this.storedCustomerId);
  },
  methods: {
    onUpdateId: function (newValue) {
      this.errorTextId = TextValidation_User.validate(newValue, "ID");
      this.customerId = newValue;
      this.enableSaveButton();
    },
    onUpdatePass: function (newValue) {
      this.errorTextPass = TextValidation_User.validate(newValue, "passkey");
      this.userPassword = newValue;
      this.enableSaveButton();
    },
    onUpdateUserName: function (newValue) {
      this.errorTextUserName = TextValidation_User.validate(newValue, "userName");
      this.userName = newValue;
      this.enableSaveButton();
    },
    clickedButton: function (choice) {
      switch (choice) {
        case 0:
          this.cancelAddUser();
          break;
        case 1:
          this.saveNewuser();
          break;
      }
    },
    cancelAddUser() {
      this.$emit("cancel-id");
    },
    saveNewuser() {
      const addUser = {
        customerId: this.customerId,
        userPassword: this.userPassword,
        userName: this.userName,
      };
      this.$emit("save-id", addUser);
    },
    enableSaveButton() {
      if (this.errorTextId === "") {
        if (this.errorTextPass === "") {
          if (this.errorTextUserName === "") {
            this.enablelistAddUser = [true, true];
            return;
          }
        }
      }
      this.enablelistAddUser = [true, false];
    },
  },
};
</script>
<style type="text/css">
.div__addUser-form-controls {
  transform: rotate(0deg);
  box-sizing: border-box;
  padding: 0px;
  margin: 0px;
  background: rgb(17, 17, 17);
  position: absolute;
  width: 500px;
  height: 401px;
  top: 0px;
  left: 0px;
  visibility: visible;
  border: 2px solid rgb(0, 0, 0);
  border-radius: 0px;
  box-shadow: none;
  z-index: 3;
  pointer-events: all;
}
.span__addUser-form-controls-content-title {
  pointer-events: all;
  line-height: 100%;
  transform: rotate(0deg);
  overflow: hidden;
  position: absolute;
  width: 500px;
  height: 30px;
  top: 17px;
  left: 0px;
  padding: 5px;
  visibility: visible;
  user-select: none;
  font-family: Muli;
  font-weight: normal;
  font-style: normal;
  text-decoration: none;
  font-size: 19px;
  color: rgb(255, 255, 255);
  text-align: center;
  z-index: 21;
}
.span__input-controls-content-input-txt-widget > #input-widget-field-username {
  font-family: Muli;
}
.span__input-user-title {
  position: absolute;
  top: -34px;
  color: #b7b7b7;
  width: 400px;
  justify-content: center;
  display: flex;
  font-size: 17px;
}
</style>
