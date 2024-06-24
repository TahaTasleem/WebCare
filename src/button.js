"use strict";

import React from "react";
import { useContext } from "react";
import { SchemeContext } from "./scheme.js";

function Button(props) {
    const scheme = useContext(SchemeContext);
    let style = { width: props.button.width, height: props.button.height };
    if (props.button.autoposition) {
        style.bottom = "5px";
        style.right = props.button.right;
    } else {
        style.left = props.button.left;
        style.top = props.button.top;
    }
    style.color = scheme?.TEXT?.colour;
    let img;
    if (props.button.filename !== "") {
        img = (
            <img
                class="buttonimage"
                src={props.button.src}
                alt={props.button.filename}
            />
        );
    }

    const setValue = (e) => {
        if (props.button.sendtype == "E") {
            WD.buttonclick(e.currentTarget, props.button.sendtext, true);
        } else {
            WD.buttonclick(e.currentTarget, props.button.sendtext);
        }
    };

    return (
        <button
            className="wdbutton btn btn-primary"
            id={props.button.id}
            style={style}
            onClick={(e) => setValue(e)}
            // Do we need this? onFocus={(e) => WD.focuselement(e, e.currentTarget.id)}
            onMouseDown={(e) => $(this).attr("click", true)}
            title={props.button.help}
            disabled={props.button.enabled ? "" : "disabled"}
        >
            {img}
            {props.button.tag}
        </button>
    );
}

export default Button;
