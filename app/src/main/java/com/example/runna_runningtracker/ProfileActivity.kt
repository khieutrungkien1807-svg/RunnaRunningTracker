package com.example.runna_runningtracker

import android.content.Intent
import android.os.Bundle
import android.view.View
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import com.example.runna_runningtracker.data.repository.AuthRepository
import com.example.runna_runningtracker.data.repository.UserRepository
import com.google.firebase.auth.FirebaseAuth

class ProfileActivity : AppCompatActivity() {

    private lateinit var tvName: TextView
    private lateinit var tvAge: TextView
    private lateinit var tvHeight: TextView
    private lateinit var tvWeight: TextView

    private lateinit var userRepo: UserRepository
    private lateinit var authRepository: AuthRepository

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_profile)

        tvName = findViewById(R.id.tvName)
        tvAge = findViewById(R.id.tvAge)
        tvHeight = findViewById(R.id.tvHeight)
        tvWeight = findViewById(R.id.tvWeight)

        userRepo = UserRepository()
        authRepository = AuthRepository()

        val navHome = findViewById<View>(R.id.navHome)
        val navStart = findViewById<View>(R.id.navStart)
        val navHistory = findViewById<View>(R.id.navHistory)
        val navProfile = findViewById<View>(R.id.navProfile)
        val tvLogout = findViewById<View>(R.id.tvLogout)

        val uid = FirebaseAuth.getInstance().currentUser?.uid ?: return

        userRepo.getUser(uid) { user ->
            if (user != null) {
                runOnUiThread {
                    tvName.text = getString(R.string.profile_name_value, user.name)
                    tvAge.text = getString(R.string.profile_age_value, user.age)
                    tvHeight.text = getString(R.string.profile_height_value, user.height)
                    tvWeight.text = getString(R.string.profile_weight_value, user.weight)
                }
            }
        }

        navHome.setOnClickListener { startActivity(Intent(this, HomeActivity::class.java)) }
        navStart.setOnClickListener { startActivity(Intent(this, StartRunningActivity::class.java)) }
        navHistory.setOnClickListener { startActivity(Intent(this, HistoryActivity::class.java)) }
        navProfile.setOnClickListener { }

        tvLogout.setOnClickListener {
            authRepository.signOut()
            startActivity(Intent(this, LoginActivity::class.java))
            finishAffinity()
        }
    }
}
