package com.example.runna_runningtracker

import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.text.SpannableString
import android.text.Spanned
import android.text.style.ForegroundColorSpan
import android.view.View
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import android.widget.Toast
import androidx.activity.enableEdgeToEdge
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat
import com.google.firebase.auth.FirebaseAuth
import com.google.firebase.firestore.FirebaseFirestore

class MainActivity : AppCompatActivity() {

    private lateinit var loginScreen: android.view.View
    private lateinit var registerScreen: android.view.View
    private lateinit var personalInfoScreen: android.view.View
    private lateinit var appScreen: android.view.View
    private lateinit var trackingScreen: android.view.View
    private lateinit var pauseOverlay: android.view.View
    private lateinit var summaryScreen: android.view.View
    private lateinit var forgotPasswordOverlay: android.view.View
    private lateinit var editProfileOverlay: android.view.View
    private lateinit var appInfoOverlay: android.view.View

    private lateinit var homeScreen: android.view.View
    private lateinit var startScreen: android.view.View
    private lateinit var historyScreen: android.view.View
    private lateinit var profileScreen: android.view.View

    private lateinit var navHome: TextView
    private lateinit var navStart: TextView
    private lateinit var navHistory: TextView
    private lateinit var navProfile: TextView

    private lateinit var typeEasy: TextView
    private lateinit var typeLong: TextView
    private lateinit var typeInterval: TextView
    private lateinit var typeWalking: TextView
    private lateinit var beginRunButton: Button
    private lateinit var runTypeChip: TextView
    private lateinit var trackingTimerText: TextView
    private lateinit var trackingStatsText: TextView
    private lateinit var pauseStatsText: TextView
    private lateinit var summaryStatsText: TextView
    private lateinit var homeWelcomeText: TextView
    private lateinit var profileInfoText: TextView
    private lateinit var recentActivityText: TextView
    private lateinit var showRegisterText: TextView

    private lateinit var registerNameInput: EditText
    private lateinit var registerEmailInput: EditText
    private lateinit var registerPasswordInput: EditText
    private lateinit var registerConfirmPasswordInput: EditText
    private lateinit var personalNameInput: EditText
    private lateinit var personalEmailInput: EditText
    private lateinit var personalAgeInput: EditText
    private lateinit var personalGenderInput: EditText
    private lateinit var personalHeightInput: EditText
    private lateinit var personalWeightInput: EditText
    private lateinit var editNameInput: EditText
    private lateinit var editEmailInput: EditText
    private lateinit var editAgeInput: EditText
    private lateinit var editGenderInput: EditText
    private lateinit var editHeightInput: EditText
    private lateinit var editWeightInput: EditText

    private lateinit var auth: FirebaseAuth
    private lateinit var firestore: FirebaseFirestore
    private val timerHandler = Handler(Looper.getMainLooper())
    private var elapsedSeconds = 2
    private var selectedRunType = "Easy"
    private var pendingRegisterUid: String? = null
    private var profileName = "Nghi"
    private var profileEmail = "nghi@gmail.com"
    private var profileAge = "19"
    private var profileGender = "Female"
    private var profileHeight = "165"
    private var profileWeight = "62"

    private val timerRunnable = object : Runnable {
        override fun run() {
            elapsedSeconds += 1
            val minutes = elapsedSeconds / 60
            val seconds = elapsedSeconds % 60
            val distance = 0.08 + (elapsedSeconds * 0.012)
            val calories = 6 + elapsedSeconds
            trackingTimerText.text = String.format("%02d:%02d", minutes, seconds)
            trackingStatsText.text = String.format("%.2f km | 5:32 pace | %d cal", distance, calories)
            pauseStatsText.text = String.format("%02d:%02d | %.2f km | 5:32 pace", minutes, seconds, distance)
            summaryStatsText.text = String.format(
                "Duration %02d:%02d\nDistance %.2f km\nAvg Pace 5:32\nCalories %d",
                minutes,
                seconds,
                distance,
                calories
            )
            timerHandler.postDelayed(this, 1000)
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContentView(R.layout.activity_main)
        ViewCompat.setOnApplyWindowInsetsListener(findViewById(R.id.main)) { view, insets ->
            val bars = insets.getInsets(WindowInsetsCompat.Type.systemBars())
            view.setPadding(bars.left, bars.top, bars.right, bars.bottom)
            insets
        }

        auth = FirebaseAuth.getInstance()
        firestore = FirebaseFirestore.getInstance()
        bindViews()
        styleInlineRegisterText()
        bindActions()
        testFirebaseConnection()
        selectSection(Section.HOME)
        selectRunType("Easy")
        checkExistingSession()
    }

    override fun onDestroy() {
        timerHandler.removeCallbacks(timerRunnable)
        super.onDestroy()
    }

    private fun bindViews() {
        loginScreen = findViewById(R.id.loginScreen)
        registerScreen = findViewById(R.id.registerScreen)
        personalInfoScreen = findViewById(R.id.personalInfoScreen)
        appScreen = findViewById(R.id.appScreen)
        trackingScreen = findViewById(R.id.trackingScreen)
        pauseOverlay = findViewById(R.id.pauseOverlay)
        summaryScreen = findViewById(R.id.summaryScreen)
        forgotPasswordOverlay = findViewById(R.id.forgotPasswordOverlay)
        editProfileOverlay = findViewById(R.id.editProfileOverlay)
        appInfoOverlay = findViewById(R.id.appInfoOverlay)

        homeScreen = findViewById(R.id.homeScreen)
        startScreen = findViewById(R.id.startScreen)
        historyScreen = findViewById(R.id.historyScreen)
        profileScreen = findViewById(R.id.profileScreen)

        navHome = findViewById(R.id.navHome)
        navStart = findViewById(R.id.navStart)
        navHistory = findViewById(R.id.navHistory)
        navProfile = findViewById(R.id.navProfile)

        typeEasy = findViewById(R.id.typeEasy)
        typeLong = findViewById(R.id.typeLong)
        typeInterval = findViewById(R.id.typeInterval)
        typeWalking = findViewById(R.id.typeWalking)
        beginRunButton = findViewById(R.id.beginRunButton)
        runTypeChip = findViewById(R.id.runTypeChip)
        trackingTimerText = findViewById(R.id.trackingTimerText)
        trackingStatsText = findViewById(R.id.trackingStatsText)
        pauseStatsText = findViewById(R.id.pauseStatsText)
        summaryStatsText = findViewById(R.id.summaryStatsText)
        homeWelcomeText = findViewById(R.id.homeWelcomeText)
        profileInfoText = findViewById(R.id.profileInfoText)
        recentActivityText = findViewById(R.id.recentActivityText)
        showRegisterText = findViewById(R.id.showRegisterText)

        registerNameInput = findViewById(R.id.registerNameInput)
        registerEmailInput = findViewById(R.id.registerEmailInput)
        registerPasswordInput = findViewById(R.id.registerPasswordInput)
        registerConfirmPasswordInput = findViewById(R.id.registerConfirmPasswordInput)
        personalNameInput = findViewById(R.id.personalNameInput)
        personalEmailInput = findViewById(R.id.personalEmailInput)
        personalAgeInput = findViewById(R.id.personalAgeInput)
        personalGenderInput = findViewById(R.id.personalGenderInput)
        personalHeightInput = findViewById(R.id.personalHeightInput)
        personalWeightInput = findViewById(R.id.personalWeightInput)
        editNameInput = findViewById(R.id.editNameInput)
        editEmailInput = findViewById(R.id.editEmailInput)
        editAgeInput = findViewById(R.id.editAgeInput)
        editGenderInput = findViewById(R.id.editGenderInput)
        editHeightInput = findViewById(R.id.editHeightInput)
        editWeightInput = findViewById(R.id.editWeightInput)
    }

    private fun bindActions() {
        showRegisterText.setOnClickListener {
            loginScreen.visibility = View.GONE
            registerScreen.visibility = View.VISIBLE
        }

        findViewById<View>(R.id.backToLoginButton).setOnClickListener {
            registerScreen.visibility = View.GONE
            loginScreen.visibility = View.VISIBLE
        }

        findViewById<TextView>(R.id.forgotPasswordText).setOnClickListener {
            forgotPasswordOverlay.visibility = View.VISIBLE
        }

        findViewById<Button>(R.id.sendResetButton).setOnClickListener {
            handleForgotPassword()
        }

        findViewById<Button>(R.id.loginButton).setOnClickListener {
            handleLogin()
        }

        findViewById<Button>(R.id.createAccountButton).setOnClickListener {
            handleRegister()
        }

        findViewById<Button>(R.id.completeProfileButton).setOnClickListener {
            completePersonalInfo()
        }

        findViewById<TextView>(R.id.logoutButton).setOnClickListener {
            timerHandler.removeCallbacks(timerRunnable)
            auth.signOut()
            appScreen.visibility = View.GONE
            trackingScreen.visibility = View.GONE
            summaryScreen.visibility = View.GONE
            pauseOverlay.visibility = View.GONE
            registerScreen.visibility = View.GONE
            personalInfoScreen.visibility = View.GONE
            editProfileOverlay.visibility = View.GONE
            appInfoOverlay.visibility = View.GONE
            loginScreen.visibility = View.VISIBLE
            findViewById<EditText>(R.id.loginEmailInput).setText("")
            findViewById<EditText>(R.id.loginPasswordInput).setText("")
        }

        findViewById<TextView>(R.id.editProfileButton).setOnClickListener {
            fillEditProfileForm()
            editProfileOverlay.visibility = View.VISIBLE
        }

        findViewById<Button>(R.id.saveProfileButton).setOnClickListener {
            saveProfile()
        }

        findViewById<TextView>(R.id.appInfoButton).setOnClickListener {
            appInfoOverlay.visibility = View.VISIBLE
        }

        findViewById<Button>(R.id.closeAppInfoButton).setOnClickListener {
            appInfoOverlay.visibility = View.GONE
        }

        navHome.setOnClickListener { selectSection(Section.HOME) }
        navStart.setOnClickListener { selectSection(Section.START) }
        navHistory.setOnClickListener { selectSection(Section.HISTORY) }
        navProfile.setOnClickListener { selectSection(Section.PROFILE) }

        findViewById<Button>(R.id.homeStartRunningButton).setOnClickListener {
            selectSection(Section.START)
        }

        typeEasy.setOnClickListener { selectRunType("Easy") }
        typeLong.setOnClickListener { selectRunType("Long") }
        typeInterval.setOnClickListener { selectRunType("Interval") }
        typeWalking.setOnClickListener { selectRunType("Walking") }

        beginRunButton.setOnClickListener {
            appScreen.visibility = View.GONE
            summaryScreen.visibility = View.GONE
            pauseOverlay.visibility = View.GONE
            trackingScreen.visibility = View.VISIBLE
            runTypeChip.text = selectedRunType
            elapsedSeconds = 2
            trackingTimerText.text = "00:02"
            timerHandler.removeCallbacks(timerRunnable)
            timerHandler.post(timerRunnable)
        }

        findViewById<Button>(R.id.pauseRunButton).setOnClickListener {
            timerHandler.removeCallbacks(timerRunnable)
            pauseOverlay.visibility = View.VISIBLE
        }

        findViewById<Button>(R.id.resumeRunButton).setOnClickListener {
            pauseOverlay.visibility = View.GONE
            timerHandler.post(timerRunnable)
        }

        findViewById<Button>(R.id.finishRunButton).setOnClickListener {
            timerHandler.removeCallbacks(timerRunnable)
            pauseOverlay.visibility = View.GONE
            trackingScreen.visibility = View.GONE
            summaryScreen.visibility = View.VISIBLE
        }

        findViewById<Button>(R.id.summaryDoneButton).setOnClickListener {
            summaryScreen.visibility = View.GONE
            appScreen.visibility = View.VISIBLE
            selectSection(Section.HOME)
        }
    }

    private fun openMainApp() {
        loginScreen.visibility = View.GONE
        registerScreen.visibility = View.GONE
        personalInfoScreen.visibility = View.GONE
        trackingScreen.visibility = View.GONE
        pauseOverlay.visibility = View.GONE
        forgotPasswordOverlay.visibility = View.GONE
        editProfileOverlay.visibility = View.GONE
        appInfoOverlay.visibility = View.GONE
        summaryScreen.visibility = View.GONE
        appScreen.visibility = View.VISIBLE
        refreshProfileUi()
        selectSection(Section.HOME)
    }

    private fun checkExistingSession() {
        val currentUser = auth.currentUser ?: return
        loginScreen.visibility = View.GONE
        registerScreen.visibility = View.GONE
        personalInfoScreen.visibility = View.GONE
        openMainApp()
        loadUserProfile(currentUser.uid)
    }

    private fun selectSection(section: Section) {
        homeScreen.visibility = if (section == Section.HOME) View.VISIBLE else View.GONE
        startScreen.visibility = if (section == Section.START) View.VISIBLE else View.GONE
        historyScreen.visibility = if (section == Section.HISTORY) View.VISIBLE else View.GONE
        profileScreen.visibility = if (section == Section.PROFILE) View.VISIBLE else View.GONE

        val primary = ContextCompat.getColor(this, R.color.runna_primary)
        val secondary = ContextCompat.getColor(this, R.color.runna_text_secondary)
        navHome.setTextColor(if (section == Section.HOME) primary else secondary)
        navStart.setTextColor(if (section == Section.START) primary else secondary)
        navHistory.setTextColor(if (section == Section.HISTORY) primary else secondary)
        navProfile.setTextColor(if (section == Section.PROFILE) primary else secondary)
    }

    private fun selectRunType(type: String) {
        selectedRunType = type
        beginRunButton.text = "Start $type Run"
        styleRunType(typeEasy, type == "Easy")
        styleRunType(typeLong, type == "Long")
        styleRunType(typeInterval, type == "Interval")
        styleRunType(typeWalking, type == "Walking")
    }

    private fun styleRunType(view: TextView, selected: Boolean) {
        if (selected) {
            view.background = ContextCompat.getDrawable(this, R.drawable.bg_button_outline)
            view.setTextColor(ContextCompat.getColor(this, R.color.runna_primary))
        } else {
            view.background = ContextCompat.getDrawable(this, R.drawable.bg_card_subtle)
            view.setTextColor(ContextCompat.getColor(this, R.color.runna_text_primary))
        }
    }

    private fun fillEditProfileForm() {
        editNameInput.setText(profileName)
        editEmailInput.setText(profileEmail)
        editAgeInput.setText(profileAge)
        editGenderInput.setText(profileGender)
        editHeightInput.setText(profileHeight)
        editWeightInput.setText(profileWeight)
    }

    private fun saveProfile() {
        profileName = editNameInput.text.toString().ifBlank { profileName }
        profileEmail = editEmailInput.text.toString().ifBlank { profileEmail }
        profileAge = editAgeInput.text.toString().ifBlank { profileAge }
        profileGender = editGenderInput.text.toString().ifBlank { profileGender }
        profileHeight = editHeightInput.text.toString().ifBlank { profileHeight }
        profileWeight = editWeightInput.text.toString().ifBlank { profileWeight }
        val uid = auth.currentUser?.uid
        if (uid == null) {
            refreshProfileUi()
            editProfileOverlay.visibility = View.GONE
            Toast.makeText(this, "Profile updated locally", Toast.LENGTH_SHORT).show()
            return
        }

        firestore.collection("users").document(uid)
            .set(buildUserMap(), com.google.firebase.firestore.SetOptions.merge())
            .addOnSuccessListener {
                refreshProfileUi()
                editProfileOverlay.visibility = View.GONE
                Toast.makeText(this, "Profile updated", Toast.LENGTH_SHORT).show()
            }
            .addOnFailureListener { error ->
                Toast.makeText(this, "Update failed: ${error.message}", Toast.LENGTH_SHORT).show()
            }
    }

    private fun refreshProfileUi() {
        homeWelcomeText.text = "Welcome back, $profileName"
        profileInfoText.text = "$profileName\n$profileEmail\nAge $profileAge | $profileGender\nHeight $profileHeight cm | Weight $profileWeight kg"
        recentActivityText.text = "Recent Activity\nEasy Run | 5.2 km | 28:45\nLong Run | 10.0 km | 58:30"
    }

    private fun styleInlineRegisterText() {
        val fullText = "Don't have an account? Register"
        val registerWord = "Register"
        val startIndex = fullText.indexOf(registerWord)
        val spannable = SpannableString(fullText)
        if (startIndex >= 0) {
            spannable.setSpan(
                ForegroundColorSpan(ContextCompat.getColor(this, R.color.runna_primary)),
                startIndex,
                startIndex + registerWord.length,
                Spanned.SPAN_EXCLUSIVE_EXCLUSIVE
            )
        }
        showRegisterText.text = spannable
    }

    private fun testFirebaseConnection() {
        FirebaseAuth.getInstance()
    }

    private fun handleLogin() {
        val email = findViewById<EditText>(R.id.loginEmailInput).text.toString().trim()
        val password = findViewById<EditText>(R.id.loginPasswordInput).text.toString().trim()

        if (email.isBlank() || password.isBlank()) {
            Toast.makeText(this, "Please enter email and password", Toast.LENGTH_SHORT).show()
            return
        }

        auth.signInWithEmailAndPassword(email, password)
            .addOnSuccessListener { result ->
                openMainApp()
                loadUserProfile(result.user?.uid)
                Toast.makeText(this, "Login successful", Toast.LENGTH_SHORT).show()
            }
            .addOnFailureListener { error ->
                Toast.makeText(this, "Login failed: ${error.message}", Toast.LENGTH_SHORT).show()
            }
    }

    private fun handleRegister() {
        val name = registerNameInput.text.toString().trim()
        val email = registerEmailInput.text.toString().trim()
        val password = registerPasswordInput.text.toString().trim()
        val confirmPassword = registerConfirmPasswordInput.text.toString().trim()

        if (name.isBlank() || email.isBlank() || password.isBlank() || confirmPassword.isBlank()) {
            Toast.makeText(this, "Please fill all register fields", Toast.LENGTH_SHORT).show()
            return
        }

        if (password.length < 6) {
            Toast.makeText(this, "Password must be at least 6 characters", Toast.LENGTH_SHORT).show()
            return
        }

        if (password != confirmPassword) {
            Toast.makeText(this, "Passwords do not match", Toast.LENGTH_SHORT).show()
            return
        }

        auth.createUserWithEmailAndPassword(email, password)
            .addOnSuccessListener { result ->
                profileName = name
                profileEmail = email
                pendingRegisterUid = result.user?.uid
                showPersonalInfoScreen(name, email)
            }
            .addOnFailureListener { error ->
                Toast.makeText(this, "Register failed: ${error.message}", Toast.LENGTH_SHORT).show()
            }
    }

    private fun handleForgotPassword() {
        val resetEmail = findViewById<EditText>(R.id.forgotPasswordEmailInput).text.toString().trim()

        if (resetEmail.isBlank()) {
            Toast.makeText(this, "Please enter your email", Toast.LENGTH_SHORT).show()
            return
        }

        auth.sendPasswordResetEmail(resetEmail)
            .addOnSuccessListener {
                forgotPasswordOverlay.visibility = View.GONE
                Toast.makeText(this, "Reset link sent to email", Toast.LENGTH_SHORT).show()
            }
            .addOnFailureListener { error ->
                Toast.makeText(this, "Reset failed: ${error.message}", Toast.LENGTH_SHORT).show()
            }
    }

    private fun createUserProfile(uid: String?, email: String, name: String) {
        if (uid == null) {
            Toast.makeText(this, "User ID not found", Toast.LENGTH_SHORT).show()
            return
        }

        val userProfile = hashMapOf(
            "name" to name,
            "email" to email,
            "age" to profileAge,
            "gender" to profileGender,
            "height" to profileHeight,
            "weight" to profileWeight
        )

        firestore.collection("users").document(uid)
            .set(userProfile)
            .addOnSuccessListener {
                openMainApp()
                loadUserProfile(uid)
                clearRegisterFields()
                Toast.makeText(this, "Register successful", Toast.LENGTH_SHORT).show()
            }
            .addOnFailureListener { error ->
                Toast.makeText(this, "Profile save failed: ${error.message}", Toast.LENGTH_SHORT).show()
            }
    }

    private fun loadUserProfile(uid: String?) {
        if (uid == null) return

        firestore.collection("users").document(uid)
            .get()
            .addOnSuccessListener { document ->
                if (!document.exists()) return@addOnSuccessListener

                profileName = document.getString("name") ?: profileName
                profileEmail = document.getString("email") ?: profileEmail
                profileAge = document.getString("age") ?: profileAge
                profileGender = document.getString("gender") ?: profileGender
                profileHeight = document.getString("height") ?: profileHeight
                profileWeight = document.getString("weight") ?: profileWeight
                refreshProfileUi()
            }
            .addOnFailureListener { error ->
                Toast.makeText(this, "Load profile failed: ${error.message}", Toast.LENGTH_SHORT).show()
            }
    }

    private fun buildUserMap(): Map<String, String> {
        return mapOf(
            "name" to profileName,
            "email" to profileEmail,
            "age" to profileAge,
            "gender" to profileGender,
            "height" to profileHeight,
            "weight" to profileWeight
        )
    }

    private fun clearRegisterFields() {
        registerNameInput.setText("")
        registerEmailInput.setText("")
        registerPasswordInput.setText("")
        registerConfirmPasswordInput.setText("")
    }

    private fun showPersonalInfoScreen(name: String, email: String) {
        loginScreen.visibility = View.GONE
        registerScreen.visibility = View.GONE
        personalInfoScreen.visibility = View.VISIBLE
        personalNameInput.setText(name)
        personalEmailInput.setText(email)
        personalAgeInput.setText(profileAge)
        personalGenderInput.setText(profileGender)
        personalHeightInput.setText(profileHeight)
        personalWeightInput.setText(profileWeight)
    }

    private fun completePersonalInfo() {
        val uid = pendingRegisterUid ?: auth.currentUser?.uid
        if (uid == null) {
            Toast.makeText(this, "Please register first", Toast.LENGTH_SHORT).show()
            return
        }

        profileName = personalNameInput.text.toString().trim().ifBlank { profileName }
        profileEmail = personalEmailInput.text.toString().trim().ifBlank { profileEmail }
        profileAge = personalAgeInput.text.toString().trim().ifBlank { profileAge }
        profileGender = personalGenderInput.text.toString().trim().ifBlank { profileGender }
        profileHeight = personalHeightInput.text.toString().trim().ifBlank { profileHeight }
        profileWeight = personalWeightInput.text.toString().trim().ifBlank { profileWeight }

        createUserProfile(uid, profileEmail, profileName)
        pendingRegisterUid = null
    }

    private enum class Section {
        HOME, START, HISTORY, PROFILE
    }
}

