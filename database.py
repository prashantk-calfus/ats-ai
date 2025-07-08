"""
Create and maintain the relational SQLite3 database for easier querying and display of candidate results.
Schema:
    uuid,
    candidate_name,
    resume_filename,
    position_applied,
    similarity_score,
    ai_comments
"""

import sqlite3
import uuid

class CandidateDB:
    def __init__(self, db_path="candidates.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.create_table()

    def create_table(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS candidates (
                    uuid TEXT PRIMARY KEY,
                    candidate_name TEXT NOT NULL,
                    resume_filename TEXT NOT NULL,
                    position_applied TEXT NOT NULL,
                    similarity_score REAL DEFAULT NULL,
                    ai_comments TEXT DEFAULT NULL
                );
            """)

    def add_candidate(self, candidate_name, resume_filename, position_applied):
        new_uuid = str(uuid.uuid4())
        with self.conn:
            self.conn.execute("""
                INSERT INTO candidates (uuid, candidate_name, resume_filename, position_applied)
                VALUES (?, ?, ?, ?)
            """, (new_uuid, candidate_name, resume_filename, position_applied))
        return new_uuid

    def get_candidate_by_uuid(self, candidate_uuid):
        cursor = self.conn.execute("""
            SELECT * FROM candidates WHERE uuid = ?
        """, (candidate_uuid,))
        return cursor.fetchone()

    def get_candidate_by_resume_filename(self, resume_filename):
        """
            Retrieves a single candidate record by their resume filename.
            Returns a tuple representing the row, or None if not found.
            Used to update the similarity_score and ai_comments field in sqlite database.
        """
        cursor = self.conn.execute("""
                   SELECT uuid, candidate_name, resume_filename, position_applied, similarity_score, ai_comments
                   FROM candidates
                   WHERE resume_filename = ?
                   """, (resume_filename,))
        return cursor.fetchone()

    def get_all_candidates(self):
        cursor = self.conn.execute("SELECT * FROM candidates")
        return cursor.fetchall()

    def update_candidate(self, candidate_uuid, candidate_name=None, resume_filename=None,
                         position_applied=None, similarity_score=None, ai_comments=None):

        """
            Single function to update any particular field or multiple fields together
        """

        fields = []
        values = []

        if candidate_name is not None:
            fields.append("candidate_name = ?")
            values.append(candidate_name)
        if resume_filename is not None:
            fields.append("resume_filename = ?")
            values.append(resume_filename)
        if position_applied is not None:
            fields.append("position_applied = ?")
            values.append(position_applied)
        if similarity_score is not None:
            fields.append("similarity_score = ?")
            values.append(similarity_score)
        if ai_comments is not None:
            fields.append("ai_comments = ?")
            values.append(ai_comments)

        if not fields:
            # No fields to update
            print("No fields provided for update.")
            return False

        values.append(candidate_uuid)
        query = f"UPDATE candidates SET {', '.join(fields)} WHERE uuid = ?"

        with self.conn:
            self.conn.execute(query, values)
        return True

    def delete_candidate(self, candidate_uuid):
        with self.conn:
            self.conn.execute("DELETE FROM candidates WHERE uuid = ?", (candidate_uuid,))
        return True

    def close(self):
        self.conn.close()


# Example usage
if __name__ == "__main__":
    db = CandidateDB()

    # Create
    uuid_ = db.add_candidate("John Doe", "john_doe_resume.pdf", "Data Scientist")
    print(f"Added candidate with UUID: {uuid_}")

    # Read all
    print("\nAll Candidates:")
    for row in db.get_all_candidates():
        print(row)

    # Read one
    print("\nSingle Candidate:")
    print(db.get_candidate_by_uuid(uuid_))

    # Update
    # db.update_candidate(uuid_, position_applied="Senior Data Scientist")

    # Read updated
    print("\nAfter Update:")
    print(db.get_candidate_by_uuid(uuid_))

    # Delete
    db.delete_candidate(uuid_)
    print("\nAfter Deletion:")
    print(db.get_candidate_by_uuid(uuid_))

    db.close()
