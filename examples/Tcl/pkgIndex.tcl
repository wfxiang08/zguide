package ifneeded mdp      1.0 [list source [file join $dir mdp.tcl]]
package ifneeded MDClient 1.0 [list source [file join $dir mdcliapi.tcl]]
package ifneeded MDClient 2.0 [list source [file join $dir mdcliapi2.tcl]]
package ifneeded MDWorker 1.0 [list source [file join $dir mdwrkapi.tcl]]
package ifneeded BStar    1.0 [list source [file join $dir bstar.tcl]]
package ifneeded FLClient 1.0 [list source [file join $dir flcliapi.tcl]]
package ifneeded KVSimple 1.0 [list source [file join $dir kvsimple.tcl]]
package ifneeded KVMsg    1.0 [list source [file join $dir kvmsg.tcl]]