"use strict";

import React from "react";
import { useContext } from "react";
import { SchemeContext } from "./scheme.js";

function Label(props) {
    const scheme = useContext(SchemeContext);
    const formattedTag = props.tag.replace('<br>', '\n');
    return (
        <label
            htmlFor={props.name}
            style={{
                top: props.top + "em",
                left: props.left + "%",
                whiteSpace: "pre-line",
                color: scheme?.TEXT?.colour,
            }}
            className="wdlabel"
        >
            {
                // Need to handle newlines here?
                formattedTag
            }
        </label>
    );
}

export default Label;
