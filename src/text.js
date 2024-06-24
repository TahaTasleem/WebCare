"use strict";

import React from "react";
import { useContext } from "react";
import { SchemeContext } from "./scheme.js";
import { convertrowunittoem } from "./utils.js";

function WDText(props) {
    const scheme = useContext(SchemeContext);
    if (props.text.heading) {
        return (
            <h4
                id={props.text.id}
                style={{
                    top: props.text.top,
                    left: props.text.left,
                    minHeight: convertrowunittoem(0.75) + "em",
                }}
                className="screencaption"
            >
                {props.text.tag}
            </h4>
        );
    } else if (props.text.texttype == "IMAGE") {
        return (
            <img
                className="image"
                src={props.text.src}
                alt={props.text.filename}
                style={{ top: props.text.top, left: props.text.left }}
            />
        );
    } else {
        return (
            <label
                className="wdlabel"
                style={{
                    top: props.text.top,
                    left: props.text.left,
                    color: scheme?.TEXT.colour,
                }}
            >
                {props.text.tag}
            </label>
        );
    }
}
export default WDText;
