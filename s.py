import sensors
import re

sensors.init()

for chip in sensors.ChipIterator("coretemp-*"):
#    import pdb; pdb.set_trace()
    rname = re.sub("-","_", sensors.chip_snprintf_name(chip))

    for feature in sensors.FeatureIterator(chip):
        sfi = sensors.SubFeatureIterator(chip, feature)
        vals = [sensors.get_value(chip, sf.number) for sf in sfi]
        label = sensors.get_label(chip, feature)
        label = re.sub("Package id ","pkg_", label)
        label = re.sub("Core ","core_", label)

        print("%s_%s: %s" % (rname, label, str(vals[0])))

sensors.cleanup()
