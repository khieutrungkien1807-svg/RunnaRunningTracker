package com.example.runna_runningtracker

import android.content.Intent
import android.os.Bundle
import android.view.View
import android.widget.Button
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import com.example.runna_runningtracker.data.repository.AuthRepository
import com.example.runna_runningtracker.data.repository.UserRepository

class HomeActivity : AppCompatActivity() {

    companion object {
        const val EXTRA_USER_ID = "extra_user_id"
    }

    private lateinit var authRepository: AuthRepository
    private lateinit var userRepository: UserRepository

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_home)

        authRepository = AuthRepository()
        userRepository = UserRepository()

        val tvWelcome = findViewById<TextView>(R.id.tvWelcome)
        val tvSubtitle = findViewById<TextView>(R.id.tvSubtitle)
        val btnStartRunning = findViewById<View>(R.id.btnStartRunning)
        val navHome = findViewById<View>(R.id.navHome)
        val navStart = findViewById<View>(R.id.navStart)
        val navHistory = findViewById<View>(R.id.navHistory)
        val navProfile = findViewById<View>(R.id.navProfile)

        val uid = intent.getStringExtra(EXTRA_USER_ID) ?: authRepository.getCurrentUserId()
        if (uid != null) {
            userRepository.loadUserProfile(
                uid = uid,
                onSuccess = { user ->
                    runOnUiThread {
                        val displayName = user.name.ifBlank { "Runner" }
                        tvWelcome.text = getString(R.string.welcome_back_home, displayName)
                        tvSubtitle.text = getString(R.string.ready_next_run)
                    }
                },
                onFailure = {
                    runOnUiThread {
                        tvWelcome.text = getString(R.string.welcome_back_home_default)
                    }
                }
            )
        }

        val btnChallengesHome = findViewById<View>(R.id.btnChallengesHome)

        btnStartRunning.setOnClickListener {
            startActivity(Intent(this, StartRunningActivity::class.java))
        }
        
        btnChallengesHome.setOnClickListener {
            startActivity(Intent(this, ChallengesActivity::class.java))
        }

        navHome.setOnClickListener { }
        navStart.setOnClickListener { startActivity(Intent(this, StartRunningActivity::class.java)) }
        navHistory.setOnClickListener { startActivity(Intent(this, HistoryActivity::class.java)) }
        navProfile.setOnClickListener { startActivity(Intent(this, ProfileActivity::class.java)) }
    }
}
