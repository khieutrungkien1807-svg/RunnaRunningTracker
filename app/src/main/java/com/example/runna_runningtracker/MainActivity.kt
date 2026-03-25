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

class MainActivity : AppCompatActivity() {

    private lateinit var loginScreen: android.view.View
    private lateinit var registerScreen: android.view.View
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

    private lateinit var editNameInput: EditText
    private lateinit var editEmailInput: EditText
    private lateinit var editAgeInput: EditText
    private lateinit var editGenderInput: EditText
    private lateinit var editHeightInput: EditText
    private lateinit var editWeightInput: EditText

    private val timerHandler = Handler(Looper.getMainLooper())
    private var elapsedSeconds = 2
    private var selectedRunType = "Easy"
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

        bindViews()
        styleInlineRegisterText()
        bindActions()
        selectSection(Section.HOME)
        selectRunType("Easy")
    }

    override fun onDestroy() {
        timerHandler.removeCallbacks(timerRunnable)
        super.onDestroy()
    }

    private fun bindViews() {
        loginScreen = findViewById(R.id.loginScreen)
        registerScreen = findViewById(R.id.registerScreen)
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

        findViewById<Button>(R.id.closeForgotPasswordButton).setOnClickListener {
            forgotPasswordOverlay.visibility = View.GONE
        }

        findViewById<Button>(R.id.sendResetButton).setOnClickListener {
            forgotPasswordOverlay.visibility = View.GONE
            Toast.makeText(this, "Reset link sent to email", Toast.LENGTH_SHORT).show()
        }

        findViewById<Button>(R.id.loginButton).setOnClickListener {
            openMainApp()
        }

        findViewById<Button>(R.id.createAccountButton).setOnClickListener {
            openMainApp()
        }

        findViewById<TextView>(R.id.logoutButton).setOnClickListener {
            timerHandler.removeCallbacks(timerRunnable)
            appScreen.visibility = View.GONE
            trackingScreen.visibility = View.GONE
            summaryScreen.visibility = View.GONE
            pauseOverlay.visibility = View.GONE
            registerScreen.visibility = View.GONE
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

        findViewById<Button>(R.id.cancelEditProfileButton).setOnClickListener {
            editProfileOverlay.visibility = View.GONE
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
        refreshProfileUi()
        editProfileOverlay.visibility = View.GONE
        Toast.makeText(this, "Profile updated", Toast.LENGTH_SHORT).show()
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

    private enum class Section {
        HOME, START, HISTORY, PROFILE
    }
}

