"use strict";

import React from "react";
import Label from "./label.js";
import { useContext, useState } from "react";
import { SchemeContext } from "./scheme.js";

function Prompt(props) {
    const scheme = useContext(SchemeContext);
    const [isMyInputFocused, setIsMyInputFocused] = useState(false);
    let classNames = "prompt";
    let bgcolour;
    let colour;

    const realprompt =
        props.prompt.prompttype == "X" ||
        (props.prompt.prompttype != "M" &&
            props.prompt.datarow >= 0 &&
            props.prompt.datarow <= props.screenendrow &&
            props.prompt.datacol >= 0);
    const isradiobutton = (props.prompt.edittype == "RADIO-BUTTON" ||
        props.prompt.edittype == "RADIO.BUTTON" ||
        props.prompt.edittype == "RADIOBTN");
    const ischeckbox = (props.prompt.edittype == "CHECKBOX");
    const isdisabled = (isradiobutton && (props.prompt.prompttype === "S") ||
        (ischeckbox && props.prompt.prompttype == "S" && props.gridcontrol == "") ||
        (!ischeckbox && !isradiobutton && props.prompt.prompttype == "S"))
    if (props.prompt.bgcolour) {
        classNames += " bgcoloured";
    }
    if (props.grid && props.row % 2 && isdisabled) {
        bgcolour = 'rgba(0, 0, 0, 0.0)';
    } else if (isMyInputFocused) {
        bgcolour = scheme?.FOCUS?.colour;
    } else if (props.prompt.bgcolour) {
        bgcolour = props.prompt.bgcolour;
    } else if (isdisabled && !props.grid) {
        bgcolour = scheme?.SHOWFIELD?.colour;
    } else {
        bgcolour = scheme?.EDITABLE?.colour;
    }
    if (props.prompt.textcolour) {
        colour = props.prompt.textcolour;
    } else {
        colour = scheme?.TEXT?.colour;
    }
    if (props.grid) {
        classNames += " gridprompt";
    }
    if (props.prompt.textcolour) {
        classNames += " textcoloured";
    }
    if (props.prompt.tlb) {
        if (props.prompt.tlbleft) {
            classNames += " tlbleft";
        } else {
            classNames += " tlbright";
        }
    }
    if (props.prompt.justification == "R") {
        classNames += " rightjustified";
    }
    if (!ischeckbox && props.prompt.checkbox) {
        classNames += " checkboxlabel"
    }
    let label;
    let prompt;

    function renderRadioButton(rbitem, index, props) {
        //This function is used in Radio Button Condition.
        //It is developed to resolve code duplication.
        return (
            <span key={index} className="inputset">
                <input
                    type="radio"
                    id={`${props.prompt.name}_${rbitem[0]}`}
                    name={props.prompt.name}
                    value={rbitem[0]}
                    disabled={isdisabled}
                    checked={rbitem[0] === decodeURIComponent(props.prompt.value)}
                    onChange={() => { }}
                    className="prompt"
                />
                <label htmlFor={`${props.prompt.name}_${rbitem[0]}`} className="rblabel" style={{ marginLeft: "3px" }}>
                    {rbitem[1]}
                </label>
                {props.prompt.radiobuttonposition === "VERTICAL" && <br />}
            </span>
        );
    }

    if (realprompt) {
        if (!props.grid && props.prompt.edittype !== "CHECKBOX") {
            label = (
                <Label
                    grid={false}
                    name={props.prompt.name}
                    top={props.prompt.labeltop}
                    left={props.prompt.labelleft}
                    tag={props.prompt.labeltag}
                />
            );
        }
        if (props.prompt.displaywidth <= 0) {
        } else if (isradiobutton) {
            if (props.prompt.radiobuttonposition === "VERTICAL") {
                prompt = (
                    <span className="promptcontainer"
                        id={props.prompt.name}
                        style={{
                            top: props.prompt.top,
                            left: props.prompt.left,
                        }}>
                        {props.prompt.radiobuttonitems.map((rbitem, index) => (
                            renderRadioButton(rbitem, index, props)
                        ))}
                    </span>
                );
            } else if (props.prompt.radiobuttonposition === "MANUAL") {
                prompt = (
                    <span id={props.prompt.name}>
                        {props.prompt.radiobuttonitems.map((rbitem, index) => (
                            <span className="promptcontainer"
                                style={{
                                    top: props.prompt.manual_top[index],
                                    left: props.prompt.manual_left[index],
                                    paddingTop: "2px",
                                }}
                                key={index}
                            >
                                {renderRadioButton(rbitem, index, props)}
                            </span>
                        ))}
                    </span>
                );
            }
        } else if (
            props.prompt.edittype == "WP" ||
            props.prompt.edittype == "WORDWRAP" ||
            props.prompt.edittype == "SCH.SCHEDULE"
        ) {
            prompt = (
                <div
                    className={`promptcontainer ${props.prompt.prompttype == "S" ? 'promptreadonly' : ''}`}
                    style={{
                        left: props.grid ? "" : props.prompt.left,
                        top: props.grid ? "" : props.prompt.top,
                        width: props.grid ? "" : props.prompt.width,
                    }}
                    title={props.prompt.title}
                >
                    <textarea
                        onDragStart={(e) => e.preventDefault()}
                        draggable="false"
                        readOnly={isdisabled}
                        className={classNames}
                        data-orig={decodeURIComponent(props.prompt.value)}
                        data-promptliteral={props.prompt.promptliteral}
                        style={{
                            overflow: "hidden",
                            backgroundColor: bgcolour,
                            color: colour,
                        }}
                        id={props.prompt.name}
                        maxLength="4096"
                        name={props.prompt.name}
                        rows={props.prompt.numrows}
                        value={decodeURIComponent(props.prompt.value)}
                        onChange={(e) =>
                            props.grid
                                ? props.setValue(
                                    props.gridindex,
                                    props.row,
                                    props.col,
                                    e.target.value
                                )
                                : props.setValue(props.index, e.target.value)
                        }
                        onBlur={() => setIsMyInputFocused(false)}
                        onFocus={() => setIsMyInputFocused(true)}
                    />
                    {props.prompt.prompttype == "S" && (
                        <div className="prompttext">
                            {decodeURIComponent(props.prompt.value)}
                        </div>
                    )}
                </div>
            );
        } else if (ischeckbox) {
            prompt = (
                <span
                    className="promptcontainer"
                    style={{
                        top: props.prompt.top,
                        left: props.prompt.left,
                        width: (props.grid ? props.prompt.width : ""),
                    }}>
                    <input
                        type="checkbox"
                        disabled={isdisabled}
                        checked={decodeURIComponent(props.prompt.value) == props.prompt.checkedvalue}
                        data-checkedvalue={props.prompt.checkedvalue}
                        data-uncheckedvalue={props.prompt.uncheckedvalue}
                        name={props.prompt.name}
                        id={props.prompt.name}
                        onChange={(event) => {
                            if (props.grid) {
                                if (!WD.focused(props.gridfocus2) && !WD.focused(props.gridfocus1)) {
                                    WD.senddata(WD.getjump(props.prompt.name));
                                }
                                WD.updateelement(event, event.target, props.prompt.rowpos);
                                event.stopPropagation();
                            } else {
                                WD.focuselement(event, event.target.id);
                                WD.updateelement(event, event.target);
                            }
                            return false;
                        }}
                        className="prompt"
                        value={props.prompt.value}
                    />
                    <label htmlFor={props.prompt.id} className="rblabel" style={{ marginLeft: "3px" }}>
                        {props.prompt.labeltag}
                    </label>
                </span>
            )
        } else if (props.prompt.edittype == "BROWSER") {
            let style = { position: "absolute" };
            let iframestyle = {};
            if (props.prompt.fullscreen) {
                style.bottom = 0;
                style.left = 0;
                style.right = 0;
                style.top = 0;
                iframestyle.border = 0;
                //TODO: check config.product somehow?
                iframestyle.marginTop = "-3px";
            } else {
                style.left = props.prompt.left;
                style.top = props.prompt.top;
                style.height = props.prompt.height;
                style.width = props.prompt.width;
            }
            let src = decodeURIComponent(props.prompt.value);
            if (
                props.prompt.cmd == "login" &&
                src !== "about:blank" &&
                src !== ""
            ) {
                src = "..\\" + src;
            }
            prompt = (
                <div id={props.prompt.name} style={style}>
                    <iframe
                        className="screenbrowser"
                        style={iframestyle}
                        src={src}
                        onLoad={(e) =>
                            WD.updateiframefunctions(e.currentTarget)
                        }
                    ></iframe>
                    <script>
                        setTimeout(WD.updateiframefunctions($("#
                        {props.prompt.name} iframe").get(0)),100);
                    </script>
                </div>
            );
        } else {
            prompt = (
                <div
                    className="promptcontainer"
                    style={{
                        left: props.grid ? "" : props.prompt.left,
                        top: props.grid ? "" : props.prompt.top,
                        width: props.grid ? "" : props.prompt.width,
                    }}
                    title={
                        props.prompt.edittype !== "PASSWORD"
                            ? props.prompt.value
                            : ""
                    }
                >
                    <input
                        autoComplete="off"
                        className={classNames}
                        data-list={
                            props.prompt.aclist
                                ? props.prompt.aclist
                                : undefined
                        }
                        data-orig={props.prompt.value}
                        data-promptliteral={props.prompt.promptliteral}
                        disabled={isdisabled}
                        draggable="false"
                        id={props.prompt.name}
                        maxLength={props.prompt.maxlength}
                        name={props.prompt.name}
                        readOnly={
                            props.prompt.edittype == "PASSWORD" &&
                            props.prompt.prompttype !== "S"
                        }
                        style={{
                            width: props.prompt.tlb
                                ? "calc(100% - 1.5em )"
                                : "100%",
                            backgroundColor: bgcolour,
                            color: colour,
                        }}
                        title={
                            props.prompt.edittype !== "PASSWORD"
                                ? props.prompt.value
                                : ""
                        }
                        type={
                            props.prompt.edittype == "PASSWORD"
                                ? "password"
                                : "text"
                        }
                        value={decodeURIComponent(props.prompt.value)}
                        onChange={(e) =>
                            props.grid
                                ? props.setValue(
                                    props.gridindex,
                                    props.row,
                                    props.col,
                                    e.target.value
                                )
                                : props.setValue(props.index, e.target.value)
                        }
                        onBlur={() => setIsMyInputFocused(false)}
                        onFocus={() => setIsMyInputFocused(true)}
                    />
                    {props.prompt.tlb && (
                        <TLB
                            promptid={props.prompt.name}
                            tlbalt={props.prompt.tlbalt}
                            tlbicon={props.prompt.tlbicon}
                            tlbleft={props.prompt.tlbleft}
                        />
                    )}
                </div>
            );
        }
    } else {
        const sentences = props.prompt.promptliteral.split("\n");
        prompt = (
            <div
                className="promptcontainer manualprompt"
                style={{ display: "none" }}
                name={props.prompt.name}
                id={props.prompt.name}
                title={props.prompt.title}
                data-edittype={props.prompt.edittype}
            >
            {sentences.map((sentence, index) => (
                <span  key={index}>
                    { sentence }
                    { <br/> }
                </span>
            ))}
            </div>
        );
    }
    return (
        <>
            {label}
            {prompt}
        </>
    );
}

function TLB(props) {
    let classnames = "btn btn-primary wdtlb ";
    if (props.tlbleft) classnames += "tlbleft";
    else classnames += "tlbright";

    let imageclassnames = "";
    let imgalt = "";

    if (props.tlbicon.includes("/calendar.svg")) {
        imageclassnames = "wdtlbicon wdtlbcalendar";
        imgalt = props.tlbicon;
    } else if (!props.tlbicon.includes("/arrow_v_217bc0.svg")) {
        imageclassnames = "wdtlbicon wdtlbcusticon";
        imgalt = props.tlbicon;
    } else {
        imageclassnames = "wdtlbicon";
        imgalt = props.tlbalt;
    }

    return (
        <button
            className={classnames}
            tabIndex="-1"
            id={props.promptid + "_tlb"}
            name={props.promptid + "_tlb"}
            onClick={(e) => WD.firetlb(e, e.currentTarget)}
        >
            <img className={imageclassnames} src={props.tlbicon} alt={imgalt} />
        </button>
    );
}

export default Prompt;
