"use strict";
// dependencies
const uuidBase62 = require("@tofandel/uuid-base62"); // External library depenency of @tofandel/uuid-base62
/* eslint-disable new-cap */
uuidBase62.customBase = new uuidBase62.baseX("23456789abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ"); // Custom Base 57 defined as per requirement.
/* eslint-enable */

/** Allows text validation for the pre-defined criteria rules applied on the text by definitions */
export class TextValidation {
  /**
   * Take the rule name and set the value for validation of strings been verfied
   *
   * @param {string}  validationRules - The string name  of the validation rules been activated
   */
  constructor(validationRules) {
    this.rule = validationRules;
  }
  /**
   * Returns the current rule active for the instance
   *
   * @return {string}
   */
  toString() {
    return `TextValidation.${this.rule}`;
  }
  /**
   * Returns the feedback text with either value of "" or text with reason for failure
   *
   * @param  {string}  text The text on which the validation rules are verified
   * @param  {string}  type The type of value being checked: ID, password, or username
   * @return {string} The string is either empty on valid and <space> or <invalid meessage>
   */
  validate(text, type) {
    let feedback = "";
    try {
      switch (this.rule) {
        case "plateBarcode":
          feedback = this.validateBarcode(text, type);
          break;
        case "uuidBase57encode":
          feedback = this.validateUuidBaseFiftysevenEncode(text);
          break;
        case "userAccountInput":
          feedback = this.validateUserAccountInput(text, type);
          break;
      }
    } catch (exception) {
      exception.err = "Not Supported " + exception.err;
      throw exception;
    }
    return feedback;
  }

  /**
   * Returns the feedback text with either value of "" or text with reason for failure
   *
   * @param  {stats} stats The stats on the value of the name lenght verification (true) is proper length else (false)
   * @param  {text}  text The value on which the validation rules are verified
   * @param  {string}  type The type of value being checked: ID, password, or username
   * @param  {len}  len The len the total length of the input
   * @return {string} The string is either empty on valid and <space> or <invalid meessage>
   */
  inputErrorfinder(stats, text, type, len) {
    let invalidText = "";
    switch (stats) {
      case true:
        invalidText = "";
        break;
      case false:
        if (len == 0) {
          invalidText = "This field is required";
        } else {
          invalidText = `The valid ${type} is min 1 charcter and max 36 charcters`;
        }
        if (len > 36) {
          invalidText = "Invalid as its more than 36 charcters";
        }
        break;
    }
    if (stats == true) {
      if (len > 0 && len < 36 && type == "ID") {
        invalidText = this.inputParser(stats, text, type, len);
      }
    }
    return invalidText;
  }
  /**
   * Returns the feedback text this is a real parser which identfies the proper error reason failure
   *
   * @param  {stats}     stats The stats on the value of the name length verification (true) is proper length else (false)
   * @param  {text}  text The name on which the validation rules are verified
   * @param  {string}  type The type of value being checked: ID, password, or username
   * @param  {len}  len The len the total length of the name
   * @return {string} The string is either empty on valid and <space> or <invalid meessage>
   */
  inputParser(stats, text, type, len) {
    let parseError = "";
    for (let i = 0; i < len; i++) {
      let scanAscii = 0;
      scanAscii = text.charCodeAt(i);
      switch (true) {
        case scanAscii == 32 && type !== "username" /* space          */:
          parseError = "This field is required. No spaces allowed";
          break;
        case scanAscii == 35: /* hash       #   */
        case scanAscii == 38: /* ampersand     & */
        case scanAscii == 40: /* parantheses (  */
        case scanAscii == 41: /* parantheses )  */
        case scanAscii == 45: /* hypen     -    */
        case scanAscii == 46: /*  period     .   */
        case scanAscii == 47: /*  forward slash / */
        case scanAscii >= 48 &&
          scanAscii <= 57: /* 0, 1, 2, 3, 4, 5, 6, 7, 8, 9  ascii of '0' is 48 and '9' is 57*/
        case scanAscii >= 65 && scanAscii <= 90: /* A ascii of 'A' is 65  Z ascii of 'Z' is 90 */
        case scanAscii == 95: /* underscore    */
        case scanAscii >= 97 && scanAscii <= 122:
          parseError = "";
          break;
        case scanAscii <= 31:
        case scanAscii == 33:
        case scanAscii == 34:
        case scanAscii == 36:
        case scanAscii == 37:
        case scanAscii == 39:
        case scanAscii >= 42 && scanAscii <= 44:
        case scanAscii >= 58 && scanAscii <= 64:
        case scanAscii >= 91 && scanAscii <= 94:
        case scanAscii == 96:
        case scanAscii >= 123:
          parseError = "Invalid character present. Valid characters are alphanumeric & # - .   ( ) /";
          i = len + 1;
          break;
      }
    }
    return parseError;
  }
  /**
   * Returns the feedback text with either value of "" or text with reason for failure
   *
   * @param  {text}  text The text on which the validation rules are verified
   * @param  {string}  type The type of value being checked: ID, password, or username
   * @return {string} The string is either empty on valid and <space> or <invalid meessage>
   */
  validateUserAccountInput(text, type) {
    let feedback = "";
    if (text != null) {
      const valLength = text.length;
      if (valLength >= 1 && valLength <= 36) {
        feedback = this.inputErrorfinder(true, text, type, valLength);
      } else {
        feedback = this.inputErrorfinder(false, text, type, valLength);
      }
    } else {
      feedback = this.inputErrorfinder(false, text, type, 0);
    }
    return feedback;
  }
  /**
   * Returns the feedback text for the plate barcode validation
   *
   * @param  {string}  barcode The barcode string to validate
   * @param {string} type The barcode type "stimBarcode" or "plateBarcode"
   * @return {string} "" if barcode is valid, " " otherwise
   *
   */
  validateBarcode(barcode, type) {
    if (barcode == null) {
      return " ";
    }
    // check that barcode is a valid length
    const plateBarcodeLen = barcode.length;
    if (plateBarcodeLen !== 12) {
      return " ";
    }
    // check barcode header
    const barcodeHeader = barcode.slice(0, 2);
    if (
      (type === "plateBarcode" && barcodeHeader !== "ML") ||
      (type === "stimBarcode" && barcodeHeader !== "MS") ||
      (barcodeHeader !== "ML" && barcodeHeader !== "MS")
    ) {
      return " ";
    }

    return barcode.includes("-") ? this.checkNewBarcode(barcode) : this.checkOldBarcode(barcode);
  }

  /**
   * Returns the feedback text for the new plate barcode validation
   *
   * @param  {string}  barcode The barcode string to validate
   * @return {string} "" if barcode is valid, " " otherwise
   *
   */
  checkNewBarcode(barcode) {
    // check that barcode is numeric exept for header and dash
    const numericBarcode = barcode.slice(2, 10) + barcode[11];
    if (isNaN(numericBarcode)) {
      return " ";
    }
    // check if dash is in correct location
    if (barcode[10] !== "-") {
      return " ";
    }
    // check if the year is 2022 or later
    if (parseInt(barcode.slice(2, 4)) < 22) {
      return " ";
    }
    // check if the day is between 1 and 365 inclusive
    if (parseInt(barcode.slice(4, 7)) < 1 || parseInt(barcode.slice(4, 7)) > 365) {
      return " ";
    }
    // check that experiment code is between 0 and 299 inclusive
    if (parseInt(barcode.slice(7, 10)) < 0 || parseInt(barcode.slice(7, 10)) > 299) {
      return " ";
    }
    // check if in beta one or two mode. if last digit invalid then mark the barcode as invalid
    if (barcode[11] !== "2") {
      return " ";
    }
    return "";
  }
  /**
   * Returns the feedback text for the old plate barcode validation
   *
   * @param  {string}  barcode The barcode string to validate
   * @return {string} "" if barcode is valid, " " otherwise
   *
   */
  checkOldBarcode(barcode) {
    const plateBarcodeLen = barcode.length;
    for (let i = 2; i < plateBarcodeLen; i++) {
      const scanAscii = barcode.charCodeAt(i);
      // check that remaining characters are numeric
      if (scanAscii < 47 || scanAscii > 58) {
        return " ";
      }
    }
    // check year is at least 2021 [4 characters]
    const yearCode = barcode.slice(2, 6);
    const year = parseInt(yearCode);
    if (year < 2021) {
      return " ";
    }
    // check julian data is in range 001 to 366 [3 characters]
    const dayCode = barcode.slice(6, 9);
    const day = parseInt(dayCode);
    if (day < 1 || day > 366) {
      return " ";
    }
    return "";
  }
  /**
   * Returns the feedback text for the uuidBase57 encoding validation
   *
   * @param  {string}  uuidtext The uuidtext on which the validation rules are verified
   * @return {string} The string is either empty on valid or invalid text
   *
   */
  validateUuidBaseFiftysevenEncode(uuidtext) {
    let invalidText = "";
    const lenUuidBase57encode = uuidtext.length;
    let encodeUuid = "";
    let decodeUuid = "";
    if (lenUuidBase57encode == 22) {
      // decode the the value provided
      try {
        // decode the the value provided
        decodeUuid = uuidBase62.decode(uuidtext);

        encodeUuid = uuidBase62.encode(decodeUuid);
        if (encodeUuid === uuidtext) {
          invalidText = this.uuidErrorfinder(lenUuidBase57encode, "valid", uuidtext);
        } else {
          invalidText = this.uuidErrorfinder(lenUuidBase57encode, "encoderror", uuidtext);
        }
      } catch (err) {
        invalidText = this.uuidErrorfinder(lenUuidBase57encode, "error", uuidtext);
      }
    } else {
      invalidText = this.uuidErrorfinder(lenUuidBase57encode, "size", uuidtext);
    }
    return invalidText;
  }
  /**
   * Returns the feedback text for the uuidBase57 encoding validation
   *
   * @param  {number}  len The len contains the length of uuidbase57 encoded data
   * @param  {string}  source The source identifies first level identified validation and errors.
   * @param  {string}  uuidtext The uuidtext on which the validation rules are verified
   * @return {string} The string is either empty on valid or invalid text with specific information.
   *
   */
  uuidErrorfinder(len, source, uuidtext) {
    let feedbackText = "";
    let invalidBuilder = "";
    for (let i = 0; i < uuidtext.length; i++) {
      const scanAscii = uuidtext.charCodeAt(i);
      if (scanAscii === 48) {
        invalidBuilder += "0,";
      } else if (scanAscii === 49) {
        invalidBuilder += "1,";
      } else if (scanAscii === 73) {
        invalidBuilder += "I,";
      } else if (scanAscii === 79) {
        invalidBuilder += "O,";
      } else if (scanAscii === 108) {
        invalidBuilder += "l,";
      }
    }
    if (len == 0) {
      feedbackText = "This field is required";
    } else if (len < 22) {
      feedbackText = "The entered ID is " + len + " characters. All valid IDs are exactly 22 characters.";
    } else if (len > 22) {
      feedbackText = "The entered ID is " + len + " characters. All valid IDs are exactly 22 characters.";
    } else if (invalidBuilder != "") {
      feedbackText = "The entered ID has an invalid character " + invalidBuilder;
    } else if (source == "error") {
      feedbackText = "Entry permitted for Alphanumeric only";
    } else if (source == "encoderror") {
      feedbackText = "This combination of 22 characters is invalid encoded id";
    } else {
      feedbackText = "";
    }
    return feedbackText;
  }
  /**
   * Returns the feedback text with either value of "" or text with reason for failure
   *
   * @param  {password}  password The password on which the validation rules are verified
   * @return {string} The string is either empty on valid and <space> or <invalid meessage>
   */
  // validateAlphanumeric(password) {
  //   let feedbackText = "";
  //   const passwordLen = password.length;
  //   let encodeUuid = "";
  //   let decodeUuid = "";
  //   if (passwordLen == 36) {
  //     // encode the the value provided
  //     try {
  //       encodeUuid = uuidBase62.encode(password);
  //       decodeUuid = uuidBase62.decode(encodeUuid);

  //       if (decodeUuid === password) {
  //         feedbackText = this.passwordErrorfinder("valid");
  //       }
  //     } catch (err) {
  //       feedbackText = this.passwordErrorfinder("error");
  //     }
  //   } else {
  //     if (passwordLen == 0) {
  //       feedbackText = "This field is required";
  //     } else {
  //       if (passwordLen > 36) {
  //         feedbackText = this.passwordErrorfinder("error");
  //       }
  //       if (passwordLen <= 35) {
  //         feedbackText = this.passwordErrorfinder("error");
  //       }
  //     }
  //   }
  //   return feedbackText;
  // }
  // /**
  //  * Returns the feedback text with either value of "" or text with reason for failure
  //  *
  //  * @param  {stats}  stats The stats on which the validation status
  //  * @return {string} The string is either empty on valid and <space> or <invalid meessage>
  //  */
  // passwordErrorfinder(stats) {
  //   let invalidText = "";
  //   switch (stats) {
  //     case "valid":
  //       invalidText = "";
  //       break;
  //     case "error":
  //       invalidText = "Wrong Format of pass Key";
  //       break;
  //   }
  //   return invalidText;
  // }
}
