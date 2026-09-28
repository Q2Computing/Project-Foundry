import CompositionSoundness
open Q2.Composition
-- Acceptable axioms: at most `propext` and `Quot.sound`.
-- `seq` and `par` results should depend on none.
#print axioms seq_sound
#print axioms seq_sound_assembly
#print axioms par_sound
#print axioms par_sound_assembly
#print axioms impls_eq_specs
#print axioms glue_sound
#print axioms glue_sound_assembly
#print axioms glue_sound_assembly_block
#print axioms glue_nested_sound
#print axioms glue_nested_sound_assembly
#print axioms seq_par_nested_sound
#print axioms seq_glue_nested_sound
#print axioms Proven.impl_eq_spec
#print axioms map_impl_eq_map_spec
#print axioms glueList_sound
#print axioms glueList_sound_assembly
#print axioms seq_as_glue
#print axioms par_as_glue
