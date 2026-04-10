package com.example.runna_runningtracker

import android.os.Bundle
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import com.example.runna_runningtracker.data.repository.UserRepository
import com.google.firebase.auth.FirebaseAuth

class ProfileActivity : AppCompatActivity() {

    private lateinit var tvName: TextView
    private lateinit var tvAge: TextView
    private lateinit var tvHeight: TextView
    private lateinit var tvWeight: TextView

    private lateinit var userRepo: UserRepository

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_profile)

        tvName = findViewById(R.id.tvName)
        tvAge = findViewById(R.id.tvAge)
        tvHeight = findViewById(R.id.tvHeight)
        tvWeight = findViewById(R.id.tvWeight)

        userRepo = UserRepository()

        val uid = FirebaseAuth.getInstance().currentUser?.uid ?: return

        userRepo.getUser(uid) { user ->
            if (user != null) {
                runOnUiThread {
                    tvName.text = "Name: ${user.name}"
                    tvAge.text = "Age: ${user.age}"
                    tvHeight.text = "Height: ${user.height} cm"
                    tvWeight.text = "Weight: ${user.weight} kg"
                }
            }
        }
    }
}