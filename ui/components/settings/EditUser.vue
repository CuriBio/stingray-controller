<template>
  <div>
    <div class="div__edituser-form-controls"></div>
    <span class="span__edituser-form-controls-content-title">
      Edit&nbsp;<wbr />User&nbsp;<wbr />Credentials
    </span>
    <div id="customerId" style="top: 50px; left: 50px; position: absolute; z-index: 24">
      <InputWidget
        :titleLabel="'Customer ID'"
        :placeholder="'ba86b8f0-6fdf-4944-87a0-8a491a19490e'"
        :invalidText="errorTextId"
        :initialValue="customerId"
        :spellcheck="false"
        :inputWidth="400"
        :domIdSuffix="'customer-id'"
        @update:value="onUpdateId($event)"
      ></InputWidget>
    </div>
    <div id="userName" style="top: 145px; left: 50px; position: absolute; z-index: 23">
      <InputWidget
        :titleLabel="'Username'"
        :placeholder="'Curi Bio User'"
        :invalidText="errorTextUserName"
        :initialValue="userName"
        :inputWidth="400"
        :domIdSuffix="'username'"
        @update:value="onUpdateUserName($event)"
      ></InputWidget>
    </div>
    <div id="passkey" style="top: 241px; left: 50px; position: absolute; z-index: 22">
      <InputWidget
        :titleLabel="'Password'"
        :placeholder="'2VSckkBYr2An3dqHEyfRRE'"
        :invalidText="errorTextPass"
        :initialValue="userPassword"
        :type="'password'"
        :spellcheck="false"
        :inputWidth="400"
        :domIdSuffix="'passkey-id'"
        @update:value="onUpdatePass($event)"
      ></InputWidget>
    </div>
    <div style="top: 350px; left: 0px; position: absolute">
      <ButtonWidget
        :buttonWidgetWidth="500"
        :buttonWidgetHeight="50"
        :buttonWidgetTop="0"
        :buttonWidgetLeft="0"
        :buttonNames="['Cancel', 'Delete ID', 'Save ID']"
        :hoverColor="['#bd4932', '#bd4932', '#19ac8a']"
        :isEnabled="enablelistEditUser"
        @btn-click="clickedButton"
      >
      </ButtonWidget>
    </div>
  </div>
</template>
<script>
import Vue from "vue";
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
const TextValidation_User = new TextValidation("userAccountInput");

export default {
  name: "EditUser",
  components: {
    InputWidget,
    ButtonWidget,
  },
  props: {
    dialogdata: { type: Object, default: null },
    openForInvalidCreds: { type: Boolean, default: false },
  },
  data() {
    return {
      customerId: this.dialogdata.customerId,
      userName: this.dialogdata.userName,
      userPassword: this.dialogdata.userPassword,
      errorTextId: "",
      errorTextPass: "",
      errorTextUserName: "",
      enablelistEditUser: [true, true, true],
    };
  },
  created() {
    if (this.openForInvalidCreds) {
      this.errorTextId = "Invalid Customer ID, Username, or Password";
      this.errorTextPass = "Invalid Customer ID, Username, or Password";
      this.errorTextUserName = "Invalid Customer ID, Username, or Password";
      this.enablelistEditUser = [true, true, false];
    }
  },
  methods: {
    onUpdateId: function (newValue) {
      this.errorTextId = TextValidation_User.validate(newValue, "ID");
      if (this.openForInvalidCreds && this.errorTextId.length === 0) {
        this.errorTextPass = "";
        this.errorTextUserName = "";
      }
      this.customerId = newValue;
      this.enableSaveButton();
    },
    onUpdatePass: function (newValue) {
      this.errorTextPass = TextValidation_User.validate(newValue, "passkey");
      if (this.openForInvalidCreds && this.errorTextPass.length === 0) {
        this.errorTextId = "";
        this.errorTextUserName = "";
      }
      this.userPassword = newValue;
      this.enableSaveButton();
    },
    onUpdateUserName: function (newValue) {
      this.errorTextUserName = TextValidation_User.validate(newValue, "userName");
      if (this.openForInvalidCreds && this.errorTextUserName.length === 0) {
        this.errorTextId = "";
        this.errorTextPass = "";
      }
      this.userName = newValue;
      this.enableSaveButton();
    },
    clickedButton: function (choice) {
      switch (choice) {
        case 0:
          this.cancelEdituser();
          break;
        case 1:
          this.deleteUser();
          break;
        case 2:
          this.saveUser();
          break;
      }
    },
    cancelEdituser() {
      this.$emit("cancel-id");
    },
    deleteUser() {
      this.$emit("delete-id");
    },
    saveUser() {
      const editUser = {
        customerId: this.customerId,
        userPassword: this.userPassword,
        userName: this.userName,
      };
      this.$emit("save-id", editUser);
    },
    enableSaveButton() {
      if (this.errorTextId === "") {
        if (this.errorTextPass === "") {
          if (this.errorTextUserName === "") {
            this.enablelistEditUser = [true, true, true];
            return;
          }
        }
      }
      this.enablelistEditUser = [true, true, false];
    },
  },
};
</script>
<style type="text/css">
.div__edituser-form-controls {
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
.span__edituser-form-controls-content-title {
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
</style>
