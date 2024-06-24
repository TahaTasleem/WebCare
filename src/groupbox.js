"use strict";

import React from "react";
import { useContext } from "react";
import { SchemeContext } from "./scheme.js";

    function GroupBox(props){
        const scheme = useContext(SchemeContext);
        return (
            <div>
                {!props.groupbox.singleline &&
                    <div
                        id={props.groupbox.id + "_border"}
                        className="groupboxborder"
                        style={{
                            height: props.groupbox.height,
                            width: props.groupbox.width,
                            top: props.groupbox.top,
                            left: props.groupbox.left,
                        }}
                    ></div>
                }
                <div
                    id={props.groupbox.id}
                    className={`groupbox ${props.groupbox.singleline ? 'singlegroupbox' : ''}`}
                    style={{
                        width: props.groupbox.width,
                        top: props.groupbox.top,
                        left: props.groupbox.left,
                        backgroundColor: scheme?.BACKGROUND?.colour,
                    }}
                >
                    <span
                        className="groupboxcaption"
                        style={{
                            backgroundColor: scheme?.isgc ? '' : scheme?.BACKGROUND?.colour
                        }}
                    >{props.groupbox.caption}</span>
                </div>
            </div>
        );
    }
    export default GroupBox;
