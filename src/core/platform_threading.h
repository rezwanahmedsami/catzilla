#ifndef PLATFORM_THREADING_H
#define PLATFORM_THREADING_H

/*
 * Cross-platform threading abstraction for Catzilla
 * Provides unified interface for pthread (Unix/Linux/macOS) and Windows threading
 */

#ifdef _WIN32
    // Windows implementation
    #include <windows.h>
    #include <synchapi.h>

    // Windows SRW lock wrapper with state tracking
    typedef struct {
        SRWLOCK lock;
        volatile int lock_state; // 0=unlocked, 1=shared, 2=exclusive
    } catzilla_rwlock_t;

    static inline int catzilla_rwlock_init(catzilla_rwlock_t* rwlock) {
        InitializeSRWLock(&rwlock->lock);
        rwlock->lock_state = 0;
        return 0;
    }

    static inline int catzilla_rwlock_destroy(catzilla_rwlock_t* rwlock) {
        // SRW locks don't need explicit destruction
        rwlock->lock_state = 0;
        return 0;
    }

    static inline int catzilla_rwlock_rdlock(catzilla_rwlock_t* rwlock) {
        AcquireSRWLockShared(&rwlock->lock);
        rwlock->lock_state = 1; // shared
        return 0;
    }

    static inline int catzilla_rwlock_wrlock(catzilla_rwlock_t* rwlock) {
        AcquireSRWLockExclusive(&rwlock->lock);
        rwlock->lock_state = 2; // exclusive
        return 0;
    }

    static inline int catzilla_rwlock_unlock(catzilla_rwlock_t* rwlock) {
        if (rwlock->lock_state == 1) {
            ReleaseSRWLockShared(&rwlock->lock);
        } else if (rwlock->lock_state == 2) {
            ReleaseSRWLockExclusive(&rwlock->lock);
        }
        rwlock->lock_state = 0;
        return 0;
    }

#else
    // Unix/Linux/macOS implementation
    #include <pthread.h>

    typedef pthread_rwlock_t catzilla_rwlock_t;

    static inline int catzilla_rwlock_init(catzilla_rwlock_t* lock) {
        return pthread_rwlock_init(lock, NULL);
    }

    static inline int catzilla_rwlock_destroy(catzilla_rwlock_t* lock) {
        return pthread_rwlock_destroy(lock);
    }

    static inline int catzilla_rwlock_rdlock(catzilla_rwlock_t* lock) {
        return pthread_rwlock_rdlock(lock);
    }

    static inline int catzilla_rwlock_wrlock(catzilla_rwlock_t* lock) {
        return pthread_rwlock_wrlock(lock);
    }

    static inline int catzilla_rwlock_unlock(catzilla_rwlock_t* lock) {
        return pthread_rwlock_unlock(lock);
    }

#endif

#endif // PLATFORM_THREADING_H
