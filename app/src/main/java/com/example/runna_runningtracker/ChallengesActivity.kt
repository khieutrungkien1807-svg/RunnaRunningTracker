package com.example.runna_runningtracker

import android.content.Intent
import android.os.Bundle
import android.view.View
import android.widget.ImageView
import androidx.appcompat.app.AppCompatActivity

class ChallengesActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_challenges)

        val navHome = findViewById<View>(R.id.navHome)
        val navHistory = findViewById<View>(R.id.navHistory)
        val navProfile = findViewById<View>(R.id.navProfile)
        
        val btnAddChallenge = findViewById<ImageView>(R.id.btnAddChallenge)
        val cardChallenge1 = findViewById<View>(R.id.cardChallenge1)

        navHome.setOnClickListener { startActivity(Intent(this, HomeActivity::class.java)) }
        navHistory.setOnClickListener { startActivity(Intent(this, HistoryActivity::class.java)) }
        navProfile.setOnClickListener { startActivity(Intent(this, ProfileActivity::class.java)) }
        
        btnAddChallenge.setOnClickListener {
            startActivity(Intent(this, CreateChallengeActivity::class.java))
        }

        cardChallenge1.setOnClickListener {
            startActivity(Intent(this, ChallengeDetailsActivity::class.java))
        }
    }
}
