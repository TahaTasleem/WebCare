/**
 * exception.js
 */

ERRORMESSAGES = {
    "WDERR-SCRIPT-001":"The host requires you to change your password.",
    "WDERR-SCRIPT-002":"User ID or Password failed.",
    "WDERR-SCRIPT-003":"Host has terminated the connection.",
    "WDERR-SCRIPT-004":"Your account is disabled.",
    "WDERR-SCRIPT-005":"The maximum number of users are already logged on the system.  Please try again later.",
    "WDERR-SCRIPT-006":"Account is invalid or doesn't exist.",
    "WDERR-SCRIPT-007":"This version of UniVerse has expired.",
    "WDERR-SCRIPT-008":"Terminal setting is not correct."
};

/*
 * Messages d'erreur en francais
 */
/*
ERRORMESSAGES = {
	"WDERR-SCRIPT-001":"Le serveur exige de changer votre mot de passe.",
	"WDERR-SCRIPT-002":"Le code d'usager ou mot de passe a &eacute;chou&eacute;.",
	"WDERR-SCRIPT-003":"Le serveur a rompu la connexion.",
	"WDERR-SCRIPT-004":"Votre code d'usager est d&eacute;sactiv&eacute;.",
	"WDERR-SCRIPT-005":"Le nombre maximal d'usagers est atteint.  Veuillez r&eacute;essayer plus tard.",
	"WDERR-SCRIPT-006":"Le compte UniVerse est invalide ou inexistant.",
	"WDERR-SCRIPT-007":"Cette version d'UniVerse a expir&eacute;.",
	"WDERR-SCRIPT-008":"Terminal setting is not correct."
};
*/

// Execute on document ready
$(function() {
	// Set URI to be parsed
	var uri = new URI(window.location.href);
	
	// Extract URI decoded parameters
	var parms = uri.query(true);
	
	// Get errmsg
	var errmsg = "";
	var errnum = parms["err"];
	if (errnum) {
		errmsg = ERRORMESSAGES[errnum];
		if (errnum == "WDERR-SCRIPT-001") {
			$("#cpbutton").removeClass("hidden");
		}
	}
	
	// Assign to page
	$("#errmsg").text(errmsg);
	$("#errnum").text(errnum);
	$("#returl").get(0).href = parms["return"];
	
	// Set password handler
	$("#cpbutton").click(function() {
		alert("Change your password!");
	});
});
